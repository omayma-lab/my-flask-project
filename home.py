from flask import Blueprint ,render_template ,session ,redirect

home =Blueprint ("home",__name__)
import os
import mysql.connector