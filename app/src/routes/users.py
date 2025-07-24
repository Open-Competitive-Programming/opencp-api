from apiflask import APIBlueprint

users_bp = APIBlueprint(
    "users_blueprint",
    __name__,
    tag={
        "name": "User Management",
        "description": "Operations related to management of users (CRUD, Authentication, Authorization)",
    },
)


@users_bp.route("/api/v1/users")
def api_get_users():
    pass
