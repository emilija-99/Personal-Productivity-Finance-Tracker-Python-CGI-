A lightweight Python CGI web application that demonstrates core full-stack concepts:

- Login & Register with secure password hashing
  Session cookies for authentication

- CRUD operations (POST, GET, PUT, DELETE) for Movies DB
SQLite database schema with simple relations

## Features
- [ ] Register with username/email/password (hashed with bcrypt)  
- [ ] Login and maintain session with secure cookies  
- [ ] Logout clears session
- [ ] Roles: Admin, Worker, User:
  - [ ] Admin can add worker, delete worker
  - [ ] Admin can add new movie
  - [ ] Admin can see all workers
  - [ ] Admin and Worker can book movie for user
  - [ ] Admin and Worker can see all movies and movies availability
  - [ ] User can book and unbook movies (max 2 movies)
  - [ ] User can see all booked movies
- [ ] Logout and remove session from table


