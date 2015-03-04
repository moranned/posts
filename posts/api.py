import json

from flask import request, Response, url_for, Flask
from jsonschema import validate, ValidationError

import models
import decorators
from posts import app
from database import session

# JSON Schema describing the structure of a post
post_schema = {
    "properties": {
        "title" : {"type" : "string"},
        "body": {"type": "string"}
    },
    "required": ["title", "body"]
}

@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_get():
  """ Get a list of posts """
  title_like = request.args.get("title_like")
  body_like = request.args.get("body_like")
  posts = session.query(models.Post)
  if body_like and title_like:
    posts = posts.filter(models.Post.title.contains(title_like)).filter(models.Post.body.contains(body_like))
  posts = posts.all()
  
  data = json.dumps([post.as_dictionary() for post in posts])
  return Response(data, 200, mimetype="application/json")

@app.route("/api/posts", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def posts_post():
  data = request.json
  
  try:
    validate(data, post_schema)
  except ValidationError as error:
    data = {"message": error.message}
    return Response(json.dumps(data), 422, mimetype="application/json")
  
  post = models.Post(title=data["title"], body=data["body"])
  session.add(post)
  session.commit()
  
  data = json.dumps(post.as_dictionary())
  headers = {"Location": url_for("post_get", id=post.id)}
  return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/api/posts/<int:id>", methods=["GET"])
def post_get(id):
    """ Single post endpoint """
    # Get the post from the database
    post = session.query(models.Post).get(id)

    # Check whether the post exists
    # If not return a 404 with a helpful message
    if not post:
        message = "Could not find post with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Return the post as JSON
    data = json.dumps(post.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts/<int:id>", methods=["PUT"])
def post_update(id):
    """ Single post endpoint """
    data = request.json
    
    try:
      validate(data, post_schema)
    except ValidationError as error:
      data = {"message": error.message}
      return Response(json.dumps(data), 422, mimetype="application/json")
    
    post = session.query(models.Post).get(id)
    session.add(post)
    session.commit()
    
    data = json.dumps(post.as_dictionary())
    return Response(data, 200, mimetype="application/json")
  
@app.route("/api/posts/<int:id>", methods=["DELETE"])
def post_delete(id):
    """ Single post endpoint """
    # Get the post from the database
    post = session.query(models.Post).get(id)

    # Check whether the post exists
    # If not return a 404 with a helpful message
    if not post:
        message = "Could not find post with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
    
    session.delete(post)
    session.commit()
    
    # Return the post as JSON
    msg = "Deleted post with id {}".format(id)
    data = json.dumps({"message": msg})
    return Response(data, 200, mimetype="application/json")
