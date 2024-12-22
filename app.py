from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, session
from config import Config
from models import db, Exercise, DailyWorkout, User
from exercise_detection import ExerciseDetector
from datetime import date, timedelta, datetime
import cv2
import numpy as np
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import pytz  # Make sure to install pytz if you haven't already


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Initialize LoginManager after creating Flask app
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

detector = ExerciseDetector()

class WorkoutSession:
    def __init__(self, exercise_id, exercise_name, target_reps):
        self.exercise_id = exercise_id
        self.exercise_name = exercise_name
        self.target_reps = target_reps
        self.current_reps = 0
        self.stage = 'init'
        self.angle = 0

current_workout = None

@app.route('/')
@login_required
def index():
    today = date.today()
    daily_workouts = DailyWorkout.query.filter_by(user_id=current_user.id, date=today).all()

    # Prepare data for display
    workout_data = []
    for workout in daily_workouts:
        remaining_reps = max(0, workout.target_reps - workout.completed_reps)
        workout_data.append({
            "exercise_id": workout.exercise.id,
            "exercise_name": workout.exercise.name,
            "target_reps": workout.target_reps,
            "completed_reps": workout.completed_reps,
            "remaining_reps": remaining_reps,
            "is_completed": workout.is_completed
        })

    # Get incomplete workouts filtered by current_user.id
    incomplete_workouts = check_incomplete_workouts(current_user.id)  # Pass current_user.id to the function

    # Check if we should show the reminder
    last_reminder_time = session.get('last_reminder_time')

    print(last_reminder_time)


    current_time = datetime.now(pytz.utc)  # Make current time aware

    # If last reminder time is not set, convert it to UTC
    if isinstance(last_reminder_time, str):  # Check if it's a string
        last_reminder_time = datetime.fromisoformat(last_reminder_time).astimezone(pytz.utc)  # Convert to aware datetime
    else:
        last_reminder_time = None  # Set to None if it's not a string

    # If last reminder time is None or more than 3 hours ago, show the reminder
    show_reminder = False
    if last_reminder_time is None or (current_time - last_reminder_time) < timedelta(minutes=1):
        show_reminder = True
        session['last_reminder_time'] = current_time.isoformat()  # Store as ISO format string

    return render_template('index.html', daily_workouts=workout_data, today=today, incomplete_workouts=incomplete_workouts, show_reminder=show_reminder)  # Pass show_reminder to the template




@app.route('/start_workout', methods=['POST'])
@login_required
def start_workout():
    global current_workout
    exercise_id = request.form.get('exercise_id')

    # Validate the selected exercise for the logged-in user
    daily_workout = DailyWorkout.query.filter_by(
        user_id=current_user.id,
        exercise_id=exercise_id,
        date=date.today()
    ).first()
    if not daily_workout:
        return jsonify({"status": "error", "message": "No workout assigned for today with this exercise"}), 400

    exercise = Exercise.query.get(exercise_id)
    if not exercise:
        return jsonify({"status": "error", "message": "Invalid exercise ID"}), 400

    # Start the workout session
    current_workout = WorkoutSession(exercise.id, exercise.name, daily_workout.target_reps)
    print(f"Starting workout: {current_workout.exercise_name}, Target Reps: {current_workout.target_reps}")

    return jsonify({
        "status": "success",
        "exercise": {
            "id": exercise.id,
            "name": exercise.name,
            "target_reps": daily_workout.target_reps
        }
    })


def generate_frames():
    global current_workout
    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    try:
        while current_workout:
            success, frame = cap.read()
            if not success or current_workout is None:
                print("Error: Failed to capture frame or workout ended.")
                break

            # Process frame
            processed_frame, angle, stage, counter = detector.process_frame(
                frame,
                current_workout.exercise_name.lower(),
                current_workout.stage,
                current_workout.current_reps
            )

            # Update workout session
            if current_workout:  # Ensure current_workout is not None
                current_workout.angle = angle
                current_workout.stage = stage
                current_workout.current_reps = counter

            # Render UI
            processed_frame = detector.render_ui(
                processed_frame,
                current_workout.current_reps if current_workout else 0,
                current_workout.stage if current_workout else 'init',
                current_workout.angle if current_workout else 0,
                frame.shape[1],
                current_workout.exercise_name if current_workout else ''
            )

            # Encode frame for streaming
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    finally:
        cap.release()
        print("Workout ended or video capture released.")


@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/end_workout', methods=['POST'])
@login_required
def end_workout():
    global current_workout
    
    if not current_workout:
        return jsonify({"status": "error", "message": "No active workout"}), 400

    daily_workout = DailyWorkout.query.filter_by(
        user_id=current_user.id,
        exercise_id=current_workout.exercise_id,
        date=date.today()
    ).first()

    if not daily_workout:
        return jsonify({"status": "error", "message": "No matching daily workout"}), 404

    # Add the current reps to the previously completed reps
    daily_workout.completed_reps += current_workout.current_reps

    # Update the is_completed status
    daily_workout.is_completed = daily_workout.completed_reps >= daily_workout.target_reps

    db.session.commit()

    reps = current_workout.current_reps
    current_workout = None

    return jsonify({"status": "success", "reps": reps})



from calendar import monthrange

# Set the timezone to Berlin
berlin_tz = pytz.timezone('Europe/Berlin')

@app.route('/calendar', methods=['GET'])
@login_required
def get_calendar():
    # Get the current date in Berlin timezone
    today = datetime.now(berlin_tz).date()
    first_day_of_month = today.replace(day=1)
    days_in_month = monthrange(today.year, today.month)[1]

    # Replace user_id with current_user.id
    daily_workouts = DailyWorkout.query.filter(
        DailyWorkout.user_id == current_user.id,
        DailyWorkout.date >= first_day_of_month,
        DailyWorkout.date <= today.replace(day=days_in_month)
    ).all()

    # Organize data by date
    calendar_data = {}
    for workout in daily_workouts:
        # Convert date to string for JSON serialization
        date_str = workout.date.strftime('%Y-%m-%d')
        if date_str not in calendar_data:
            calendar_data[date_str] = []
        calendar_data[date_str].append({
            "exercise_name": workout.exercise.name,
            "target_reps": workout.target_reps,
            "completed_reps": workout.completed_reps,
            "is_completed": workout.is_completed
        })

    # Return calendar data as JSON
    return jsonify({
        "status": "success",
        "calendar_data": calendar_data,
        "days_in_month": days_in_month,
        "start_weekday": first_day_of_month.weekday()
    })




def create_dummy_data():
    print(f"Database URI: {Config.SQLALCHEMY_DATABASE_URI}")
    db.create_all()  # Ensure tables are created

    # Create dummy users
    if User.query.count() == 0:
        users = [
            {'name': 'John Doe', 'email': 'john@example.com', 'password': 'password123'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'password': 'password456'},
            {'name': 'Alice Johnson', 'email': 'alice@example.com', 'password': 'password789'}
        ]
        for user_data in users:
            user = User(name=user_data['name'], email=user_data['email'])
            user.set_password(user_data['password'])
            db.session.add(user)
        db.session.commit()

    # Create dummy exercises
    if Exercise.query.count() == 0:
        exercises = [
            {'name': 'squats', 'description': 'A lower-body strength exercise.'},
            {'name': 'bicep_curls', 'description': 'An arm-strengthening exercise.'},
            {'name': 'push_ups', 'description': 'A full-body exercise for core and upper body.'}
        ]
        for exercise_data in exercises:
            db.session.add(Exercise(name=exercise_data['name'], description=exercise_data['description']))
        db.session.commit()

    # Create dummy daily workouts for users
    if DailyWorkout.query.count() == 0:
        today = date.today()
        users = User.query.all()
        exercises = Exercise.query.all()

        for user in users:
            for day_offset in range(7):  # Generate workouts for the next 7 days
                workout_date = today + timedelta(days=day_offset)
                for exercise in exercises:
                    db.session.add(DailyWorkout(
                        user_id=user.id,
                        exercise_id=exercise.id,
                        date=workout_date,
                        target_reps=10 + day_offset * 2,  # Example varying target reps
                    ))
        db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
            
        return render_template('login.html', error="Invalid email or password")
        
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Function to check incomplete workouts for a specific user
def check_incomplete_workouts(user_id):
    today = date.today()
    daily_workouts = DailyWorkout.query.filter_by(user_id=user_id, date=today).all()
    incomplete_workouts = [
        {
            "exercise_name": workout.exercise.name,
            "remaining_reps": workout.target_reps - workout.completed_reps
        }
        for workout in daily_workouts if not workout.is_completed
    ]
    
    if incomplete_workouts:
        print(f"Reminder for user ID {user_id}: You have incomplete workouts for today:")
        for workout in incomplete_workouts:
            print(f"{workout['exercise_name']}: {workout['remaining_reps']} reps remaining")


if __name__ == '__main__':
    with app.app_context():
        create_dummy_data()
    app.run(debug=True)
