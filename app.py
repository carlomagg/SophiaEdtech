from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
import jwt
import datetime
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '8Zn9Ql0gTvRqW3EzDX4uKX0nPjVqRnGp'
app.config['UPLOAD_FOLDER'] = 'uploads/profile_images'


db = SQLAlchemy(app)






# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(500), nullable=True)
    profile_image = db.Column(db.String(200), nullable=True)

    location = db.relationship('Location', backref='user', uselist=False)
    education = db.relationship('Education', backref='user')
    work_experience = db.relationship('WorkExperience', backref='user')
    licenses_certifications = db.relationship('LicenseCertification', backref='user')
    enrolled_courses = db.relationship('Course', secondary=lambda: enrollment_table, lazy='subquery', backref=db.backref('enrolled_users', lazy='dynamic'))

    def __repr__(self):
        return f'<User {self.email}>'



# Location model
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    country_region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)

# Education model
class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    school = db.Column(db.String(100), nullable=True)
    degree = db.Column(db.String(100), nullable=True)
    field_of_study = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

# Work Experience model
class WorkExperience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    company = db.Column(db.String(100), nullable=True)
    role_title = db.Column(db.String(100), nullable=True)
    job_description = db.Column(db.String(500), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

# License and Certification model
class LicenseCertification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=True)
    issuing_organization = db.Column(db.String(100), nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    credentials_id = db.Column(db.String(100), nullable=True)
    credential_url = db.Column(db.String(200), nullable=True)

    # Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    content = db.Column(db.Text, nullable=False)

    # BlogPost model
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    time_read = db.Column(db.Integer, nullable=False)  # in minutes
    date = db.Column(db.Date, nullable=False, default=datetime.date.today())
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<BlogPost {self.title}>'


# Course model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    video = db.Column(db.String(200), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('courses', lazy='dynamic'))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    categories = db.relationship('CourseCategory', backref='course', lazy='dynamic')
    modules = db.relationship('Module', backref='course', lazy='dynamic')

# Module model
class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

# CourseCategory model
class CourseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

# Enrollment model
enrollment_table = db.Table('enrollment',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)


 
# Course endpoints
@app.route('/courses', methods=['POST'])
def create_course():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
        author_id = data['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.get_json()
    title = data.get('title')
    image = data.get('image')
    content = data.get('content')
    video = data.get('video')
    category_names = data.get('categories', [])
    module_names = data.get('modules', [])

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    course = Course(title=title, image=image, content=content, video=video, author_id=author_id)

    for category_name in category_names:
        category = CourseCategory(name=category_name)
        course.categories.append(category)

    for module_name in module_names:
        module = Module(name=module_name)
        course.modules.append(module)

    db.session.add(course)
    db.session.commit()

    return jsonify({'message': 'Course created successfully'}), 201
   

   # Get all courses
@app.route('/courses', methods=['GET'])
def get_courses():
    courses = Course.query.all()
    courses_data = [{'id': course.id, 'title': course.title, 'image': course.image, 'content': course.content,
                     'video': course.video, 'author': course.author.full_name, 'date_created': course.date_created,
                     'categories': [category.name for category in course.categories],
                     'modules': [module.name for module in course.modules]} for course in courses]
    return jsonify(courses_data), 200

# Get a specific course
@app.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    course_data = {'id': course.id, 'title': course.title, 'image': course.image, 'content': course.content,
                   'video': course.video, 'author': course.author.full_name, 'date_created': course.date_created,
                   'categories': [category.name for category in course.categories],
                   'modules': [module.name for module in course.modules]}
    return jsonify(course_data), 200

# Update a course
@app.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):


# Delete a course
 @app.route('/courses/<int:course_id>', methods=['DELETE'])
 def delete_course(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    db.session.delete(course)
    db.session.commit()

    return jsonify({'message': 'Course deleted successfully'}), 200
 
  # Create a new category
  # Create a new category
@app.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Category name is required'}), 400

    category = CourseCategory(name=name)
    db.session.add(category)
    db.session.commit()

    return jsonify({'message': 'Category created successfully'}), 201

# Get all categories
@app.route('/categories', methods=['GET'])
def get_categories():
    categories = CourseCategory.query.all()
    categories_data = [{'id': category.id, 'name': category.name} for category in categories]
    return jsonify(categories_data), 200

# Update a category
@app.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = CourseCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    data = request.get_json()
    name = data.get('name', category.name)

    category.name = name
    db.session.commit()

    return jsonify({'message': 'Category updated successfully'}), 200

# Delete a category
@app.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = CourseCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    db.session.delete(category)
    db.session.commit()

    return jsonify({'message': 'Category deleted successfully'}), 200


# Create a new module
@app.route('/modules', methods=['POST'])
def create_module():
    data = request.get_json()
    name = data.get('name')
    course_id = data.get('course_id')

    if not name or not course_id:
        return jsonify({'error': 'Module name and course ID are required'}), 400

    module = Module(name=name, course_id=course_id)
    db.session.add(module)
    db.session.commit()

    return jsonify({'message': 'Module created successfully'}), 201

# Get all modules
@app.route('/modules', methods=['GET'])
def get_modules():
    modules = Module.query.all()
    modules_data = [{'id': module.id, 'name': module.name, 'course_id': module.course_id} for module in modules]
    return jsonify(modules_data), 200

# Update a module
@app.route('/modules/<int:module_id>', methods=['PUT'])
def update_module(module_id):
    module = Module.query.get(module_id)
    if not module:
        return jsonify({'error': 'Module not found'}), 404

    data = request.get_json()
    name = data.get('name', module.name)
    course_id = data.get('course_id', module.course_id)

    module.name = name
    module.course_id = course_id
    db.session.commit()

    return jsonify({'message': 'Module updated successfully'}), 200

# Delete a module
@app.route('/modules/<int:module_id>', methods=['DELETE'])
def delete_module(module_id):
    module = Module.query.get(module_id)
    if not module:
        return jsonify({'error': 'Module not found'}), 404

    db.session.delete(module)
    db.session.commit()

    return jsonify({'message': 'Module deleted successfully'}), 200


    # Enroll in a course
@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
def enroll_in_course(course_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Add the course to the user's enrolled courses (you might need to create a new table or relationship for this)
    user.enrolled_courses.append(course)
    db.session.commit()

    return jsonify({'message': 'Enrolled in the course successfully'}), 200


    # Define upload directory for course videos
COURSE_VIDEO_UPLOAD_FOLDER = 'uploads/course_videos'
app.config['COURSE_VIDEO_UPLOAD_FOLDER'] = COURSE_VIDEO_UPLOAD_FOLDER

# Route to handle course video uploads
@app.route('/upload_course_video/<int:course_id>', methods=['POST'])
def upload_course_video(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['COURSE_VIDEO_UPLOAD_FOLDER'], filename))
        course.video = os.path.join(app.config['COURSE_VIDEO_UPLOAD_FOLDER'], filename)
        db.session.commit()
        return jsonify({'message': 'Course video uploaded successfully'}), 200
    else:
        return jsonify({'error': 'Upload failed'}), 500



     


# Register endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not full_name or not email or not password or not confirm_password:
        return jsonify({'error': 'All fields are required'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(full_name=full_name, email=email, password=password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or user.password != password:
        return jsonify({'error': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    return jsonify({'token': token}), 200

# Profile starts here
@app.route('/profile', methods=['GET', 'PUT'])
def profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'GET':
        user_data = {
            'full_name': user.full_name,
            'email': user.email,
            'bio': user.bio,
            'profile_image': user.profile_image,
            'location': {
                'country_region': user.location.country_region if user.location else None,
                'city': user.location.city if user.location else None
            },
            'education': [
                {
                    'id': education.id,
                    'school': education.school,
                    'degree': education.degree,
                    'field_of_study': education.field_of_study,
                    'start_date': education.start_date.isoformat() if education.start_date else None,
                    'end_date': education.end_date.isoformat() if education.end_date else None
                } for education in user.education
            ],
            'work_experience': [
                {
                    'id': work.id,
                    'company': work.company,
                    'role_title': work.role_title,
                    'job_description': work.job_description,
                    'start_date': work.start_date.isoformat() if work.start_date else None,
                    'end_date': work.end_date.isoformat() if work.end_date else None
                } for work in user.work_experience
            ],
            'licenses_certifications': [
                {
                    'id': license.id,
                    'name': license.name,
                    'issuing_organization': license.issuing_organization,
                    'issue_date': license.issue_date.isoformat() if license.issue_date else None,
                    'expiration_date': license.expiration_date.isoformat() if license.expiration_date else None,
                    'credentials_id': license.credentials_id,
                    'credential_url': license.credential_url
                } for license in user.licenses_certifications
            ]
        }
        return jsonify(user_data), 200

    if request.method == 'PUT':
        data = request.get_json()

        user.full_name = data.get('full_name', user.full_name)
        user.bio = data.get('bio', user.bio)
        user.profile_image = data.get('profile_image', user.profile_image)

        location_data = data.get('location', {})
        if user.location:
            user.location.country_region = location_data.get('country_region', user.location.country_region)
            user.location.city = location_data.get('city', user.location.city)
        else:
            user.location = Location(
                country_region=location_data.get('country_region'),
                city=location_data.get('city')
            )

        # Update education
        education_data = data.get('education', [])
        for edu_data in education_data:
            education_id = edu_data.get('id')
            if education_id:
                education = Education.query.get(education_id)
                if education:
                    education.school = edu_data.get('school', education.school)
                    education.degree = edu_data.get('degree', education.degree)
                    education.field_of_study = edu_data.get('field_of_study', education.field_of_study)
                    education.start_date = datetime.datetime.fromisoformat(edu_data.get('start_date')) if edu_data.get('start_date') else None
                    education.end_date = datetime.datetime.fromisoformat(edu_data.get('end_date')) if edu_data.get('end_date') else None
            else:
                education = Education(
                    user_id=user.id,
                    school=edu_data.get('school'),
                    degree=edu_data.get('degree'),
                    field_of_study=edu_data.get('field_of_study'),
                    start_date=datetime.datetime.fromisoformat(edu_data.get('start_date')) if edu_data.get('start_date') else None,
                    end_date=datetime.datetime.fromisoformat(edu_data.get('end_date')) if edu_data.get('end_date') else None
                )
                user.education.append(education)

        # Update work experience
        work_experience_data = data.get('work_experience', [])
        for work_data in work_experience_data:
            work_id = work_data.get('id')
            if work_id:
                work = WorkExperience.query.get(work_id)
                if work:
                    work.company = work_data.get('company', work.company)
                    work.role_title = work_data.get('role_title', work.role_title)
                    work.job_description = work_data.get('job_description', work.job_description)
                    work.start_date = datetime.datetime.fromisoformat(work_data.get('start_date')) if work_data.get('start_date') else None
                    work.end_date = datetime.datetime.fromisoformat(work_data.get('end_date')) if work_data.get('end_date') else None
            else:
                work = WorkExperience(
                    user_id=user.id,
                    company=work_data.get('company'),
                    role_title=work_data.get('role_title'),
                    job_description=work_data.get('job_description'),
                    start_date=datetime.datetime.fromisoformat(work_data.get('start_date')) if work_data.get('start_date') else None,
                    end_date=datetime.datetime.fromisoformat(work_data.get('end_date')) if work_data.get('end_date') else None
                )
                user.work_experience.append(work)

        # Update licenses and certifications
        licenses_certifications_data = data.get('licenses_certifications', [])
        for license_data in licenses_certifications_data:
            license_id = license_data.get('id')
            if license_id:
                license = LicenseCertification.query.get(license_id)
                if license:
                    license.name = license_data.get('name', license.name)
                    license.issuing_organization = license_data.get('issuing_organization', license.issuing_organization)
                    license.issue_date = datetime.datetime.fromisoformat(license_data.get('issue_date')) if license_data.get('issue_date') else None
                    license.expiration_date = datetime.datetime.fromisoformat(license_data.get('expiration_date')) if license_data.get('expiration_date') else None
                    license.credentials_id = license_data.get('credentials_id', license.credentials_id)
                    license.credential_url = license_data.get('credential_url', license.credential_url)
            else:
                license = LicenseCertification(
                    user_id=user.id,
                    name=license_data.get('name'),
                    issuing_organization=license_data.get('issuing_organization'),
                    issue_date=datetime.datetime.fromisoformat(license_data.get('issue_date')) if license_data.get('issue_date') else None,
                    expiration_date=datetime.datetime.fromisoformat(license_data.get('expiration_date')) if license_data.get('expiration_date') else None,
                    credentials_id=license_data.get('credentials_id'),
                    credential_url=license_data.get('credential_url')
                )
                user.licenses_certifications.append(license)

        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200

# Profile code ends here






# Endpoint to send a message
@app.route('/send_message', methods=['POST'])
def send_message():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
        sender_id = data['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.get_json()
    recipient_id = data.get('recipient_id')
    content = data.get('content')

    if not recipient_id or not content:
        return jsonify({'error': 'Recipient ID and message content are required'}), 400

    message = Message(sender_id=sender_id, recipient_id=recipient_id, content=content)
    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully'}), 201

# Endpoint to get messages for a user
@app.route('/get_messages/<int:user_id>', methods=['GET'])
def get_messages(user_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
        requesting_user_id = data['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    if requesting_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    messages_sent = Message.query.filter_by(sender_id=user_id).all()
    messages_received = Message.query.filter_by(recipient_id=user_id).all()

    sent_messages_data = [{'sender_id': msg.sender_id, 'timestamp': msg.timestamp, 'content': msg.content} for msg in messages_sent]
    received_messages_data = [{'sender_id': msg.sender_id, 'timestamp': msg.timestamp, 'content': msg.content} for msg in messages_received]

    return jsonify({'sent_messages': sent_messages_data, 'received_messages': received_messages_data}), 200

# Endpoint to send a message Ends Here

# Define upload directory# Define upload directory
UPLOAD_FOLDER = 'uploads/profile_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to get user ID (this is just a placeholder, replace with your actual implementation)
def get_user_id_somehow():
    # For demonstration purposes, let's assume the user ID is submitted in the request form
    user_id = request.form.get('user_id')  
    return user_id

# Route to handle profile image uploads
@app.route('/upload_profile_image', methods=['POST'])
def upload_profile_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Save the image path to the database
        user_id = get_user_id_somehow()  # Call the function to get the user ID
        user = User.query.get(user_id)
        user.profile_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        db.session.commit()
        return jsonify({'message': 'Profile image uploaded successfully'}), 200
    else:
        return jsonify({'error': 'Upload failed'}), 500
    
     # Image upolad function ends here


# Endpoint for Creating Blog Posts

    @app.route('/create_blog_post', methods=['POST'])
    def create_blog_post():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401

    try:
        data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
        author_id = data['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.get_json()
    title = data.get('title')
    image = data.get('image')
    category = data.get('category')
    time_read = data.get('time_read')

    if not title or not category or not time_read:
        return jsonify({'error': 'Title, category, and time read are required'}), 400

    blog_post = BlogPost(title=title, image=image, category=category, time_read=time_read, author_id=author_id)
    db.session.add(blog_post)
    db.session.commit()

    return jsonify({'message': 'Blog post created successfully'}), 201





    # Endpoint for Retrieving Blog Posts
    @app.route('/blog_posts', methods=['GET'])
    def get_blog_posts():
        blog_posts = BlogPost.query.all()
    blog_posts_data = [{
        'id': post.id,
        'title': post.title,
        'image': post.image,
        'category': post.category,
        'time_read': post.time_read,
        'date': post.date.isoformat(),
        'author': post.author.full_name if post.author else None
    } for post in blog_posts]

    return jsonify(blog_posts_data), 200

  






if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



