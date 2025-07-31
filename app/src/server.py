"""
Server
"""

import os

from apiflask import APIFlask

#################### BLUEPRINT IMPORTS #####################
# Import the blueprints for the logical parts of the API

from routes.users import users


############################################################

# Create an instance of this API; by default, its OpenAPI-compliant specification will be generated under folder /specs
app = APIFlask(__name__, spec_path="/specs", docs_path="/docs")

app.secret_key = os.getenv("SECRET_KEY", "1234")

app.config.from_prefixed_env()

################## BLUEPRINT REGISTRATION ##################

# Blueprints are used to split the API into logical parts,
# such as User Management, Catalog Management,
# Workflow/Execution management etc.

app.register_blueprint(users, url_prefix="/api/v1/users")

############################################################


def main(app):

    app.config["settings"] = {
        "FLASK_RUN_HOST": os.getenv("FLASK_RUN_HOST", "0.0.0.0"),
        "FLASK_RUN_PORT": os.getenv("FLASK_RUN_PORT", "80"),
        "FLASK_DEBUG": os.getenv("FLASK_DEBUG", "True") == "True",
        "API_TITLE": os.getenv("API_TITLE", "Unknown"),
        "API_VERSION": os.getenv("API_VERSION", "0.0.0"),
        "SPEC_FORMAT": os.getenv("API_SPEC_FORMAT", "json"),
        "AUTO_SERVERS": os.getenv("API_AUTO_SERVERS", "True") == "True",
        "AUTO_TAGS": os.getenv("API_AUTO_TAGS", "False") == "True",
        "AUTO_OPERATION_SUMMARY": os.getenv("API_AUTO_OPERATION_SUMMARY", "True")
        == "True",
        "AUTO_OPERATION_DESCRIPTION": os.getenv(
            "API_AUTO_OPERATION_DESCRIPTION", "True"
        )
        == "True",
    }

    # Apply configuration settings for this API
    app.title = app.config["settings"]["API_TITLE"]
    app.version = app.config["settings"]["API_VERSION"]
    app.config["SECURITY_SCHEMES"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }


def create_app():
    main(app)
    return app
