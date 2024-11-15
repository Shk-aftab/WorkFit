# WorkFit

## Project Overview
The Employee Wellness Web App, **WorkFit**, is designed to promote employees' physical well-being by offering personalized exercise routines, tracking activity, and providing real-time feedback using AI-based keypoint detection. Users can log their activities, receive reminders, and view progress through a comprehensive dashboard.

---

## Functional Requirements

### 1. **User Authentication**
   - Users can **log in** and **log out** securely.
   - Password management with encryption.
   - Session management to maintain user state.

### 2. **Dashboard**
   - Displays daily exercise routine and completion status.
   - Metrics showing user progress (e.g., weekly and monthly activity graphs).
   - Accessible through a clean and responsive interface.

### 3. **Calendar View**
   - Shows daily exercise routines.
   - Users can click on specific exercises for more details (e.g., instructions, duration).
   - Mark exercises as **complete**.

### 4. **Exercise Tracking**
   - AI model (using TensorFlow.js) accesses the webcam to:
     - Detect and count repetitions of specific exercises.
     - Provide real-time feedback on form and posture using keypoint detection.

### 5. **Notifications**
   - Send reminders for pending exercises.
   - Provide motivational messages to encourage consistency.

---

## Additional Requirements

### 1. **Analytics & Metrics**
   - Graphs and charts displaying:
     - Daily, weekly, and monthly exercise completion.
     - Calories burned (calculated based on activity type and user profile).
     - Time spent on exercises.

### 2. **Real-time Feedback**
   - Visual indicators (e.g., overlayed keypoints) showing exercise accuracy.
   - Text or audio suggestions for improving posture.

### 3. **Notifications Module**
   - Push notifications or email alerts for:
     - Missed exercises.
     - Milestone achievements.

---

## Technology Stack

### **Frontend**
   - **HTML/CSS**: Structure and styling of the web app.
   - **JavaScript**: Client-side logic.
   - **TensorFlow.js**: Real-time keypoint detection using the webcam.
   - **Bootstrap** (optional): To enhance UI responsiveness and usability.

### **Backend**
   - **Flask**: Backend framework for handling requests and responses.
   - **SQL** (PostgreSQL/MySQL): Database to store user data, exercise routines, and activity logs.
   - **RESTful APIs**: For communication between frontend and backend.

### **Additional Tools**
   - **Chart.js/D3.js**: For rendering progress metrics and graphs.
   - **TensorFlow** (for initial model training): Build and export models for keypoint detection.
   - **Nginx/Gunicorn**: For deploying the Flask application in a production environment.

---

## Implementation Phase

### 1. **Planning and Requirement Gathering**
   - Define detailed user stories and scenarios.
   - Finalize the tech stack and set up project environments.

### 2. **Backend Development**
   - **Set up Flask app**:
     - Configure routes for user authentication, dashboard, calendar, and exercise tracking.
     - Develop RESTful APIs for frontend integration.
   - **Database Design**:
     - Tables for users, exercises, progress logs, and notifications.
     - Ensure data integrity and implement necessary constraints.

### 3. **Frontend Development**
   - **HTML/CSS**:
     - Create responsive pages for login, dashboard, and calendar.
   - **JavaScript Integration**:
     - Implement interactivity for calendar and dashboard.
     - Integrate TensorFlow.js for real-time keypoint detection.
   - **Charts & Metrics**:
     - Use Chart.js to render graphs and progress metrics.

### 4. **AI Model Integration**
   - **TensorFlow Model**:
     - Train or fine-tune a keypoint detection model (if needed).
     - Export the model to TensorFlow.js for browser-based inference.
   - **Real-time Detection**:
     - Implement webcam integration to detect and count exercise repetitions.
     - Provide real-time feedback using overlays and alerts.

### 5. **Notification System**
   - Develop logic to send reminders and milestone achievements.
   - Integrate push notifications or email services (e.g., Twilio SendGrid).

### 6. **Testing**
   - **Unit Testing**: Validate individual components.
   - **Integration Testing**: Ensure smooth interaction between frontend, backend, and AI models.
   - **User Testing**: Conduct usability tests with a group of users to gather feedback.

### 7. **Deployment**
   - Deploy the app using **Nginx** and **Gunicorn** for production.
   - Host on a cloud platform (e.g., AWS, Heroku).
   - Implement CI/CD pipelines for seamless updates.

### 8. **Maintenance and Iteration**
   - Monitor application performance.
   - Collect user feedback for future improvements.
   - Add new features like more detailed analytics or new exercise routines.
