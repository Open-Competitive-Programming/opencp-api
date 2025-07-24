from flask import request, jsonify, current_app, url_for
from apiflask import APIBlueprint
import requests
import logging 
import xml.etree.ElementTree as ET
import kutils

users_bp = APIBlueprint('users_blueprint', __name__, tag={'name':'User Management','description':'Operations related to management of users (CRUD, Authentication, Authorization)'})
