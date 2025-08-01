# Open-CP API

- `/api`
  - 🔐 `/auth`
    - `POST /token` → Generate token
  - 📘 `/problemset`
    - `GET /` → Get all problems
    - `POST /` → Create a problem
    - `GET /<problem_id>` → Get problem
    - `PATCH /<problem_id>` → Update problem
    - `DELETE /<problem_id>` → Delete problem
    - `GET /<problem_id>/submissions` → Get submissions
    - `GET /<problem_id>/submissions/<id>` → Get a submission
    - `POST /submit/<problem_id>` → Submit code
  - 👤 `/users`
    - `GET /` → Get all users
    - `POST /` → Create user
    - `GET /<user_id>` → Get user
    - `PATCH /<user_id>` → Update user
    - `DELETE /<user_id>` → Delete user
