import unittest
import os
import json
from urlparse import urlparse

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

    def testGetEmptyPosts(self):
      """ Getting posts from an empty database """
      response = self.client.get("/api/posts", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data, [])
        
    def testGetPost(self):
      """ Getting a single post from a populated database """
      postA = models.Post(title="Example Post A", body="Just a test")
      postB = models.Post(title="Example Post B", body="Still a test")

      session.add_all([postA, postB])
      session.commit()

      response = self.client.get("/api/posts/{}".format(postB.id))

      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")

      post = json.loads(response.data)
      self.assertEqual(post["title"], "Example Post B")
      self.assertEqual(post["body"], "Still a test")

    def testPut(self):
      """ Updating a single post from a populated database """
      
      #Add a POST to db via SQL Alchemy
      post = models.Post(title="Example Post", body="Just a test")
      session.add(post)
      session.commit()
      
      postid = post.id
      
      #Update POST entry to DB via SQL Alchemy
      response = self.client.get("/api/posts/{}".format(postid))
      
      #Test response codes and content types
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      post = json.loads(response.data)
      self.assertEqual(post["title"], "Example Post")
      self.assertEqual(post["body"], "Just a test")
      
      #Get the existing post object from the model
      posts = session.query(models.Post)
      updatePost = posts.filter(models.Post.id == postid).first()
      
      #Update the existing Post object and store in DB
      updatePost.title = "Updated Example Post"
      updatePost.body = "Updated Body test"
      session.merge(updatePost)
      session.commit()
      
      #Get and Test updated POST via enpoint      
      putresponse = self.client.put("/api/posts/{}".format(postid))
      
      self.assertEqual(putresponse.status_code, 200)
      self.assertEqual(putresponse.mimetype, "application/json")
      newpost = json.loads(putresponse.data)
      self.assertEqual(newpost["title"], "Updated Example Post")
      self.assertEqual(newpost["body"], "Updated Body test")
      
    def testDeletePost(self):
      """ Getting a single post from a populated database """
      postA = models.Post(title="Example Post A", body="Just a test")
      postB = models.Post(title="Example Post B", body="Still a test")

      session.add_all([postA, postB])
      session.commit()

      response = self.client.delete("/api/posts/{}".format(postA.id))

      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")

      data = json.loads(response.data)
      self.assertEqual(data["message"], "Deleted post with id 1")
      
    def testGetNonExistentPost(self):
      """ Getting a single post which doesn't exist """
      response = self.client.get("/api/posts/1")

      self.assertEqual(response.status_code, 404)
      self.assertEqual(response.mimetype, "application/json")

      data = json.loads(response.data)
      self.assertEqual(data["message"], "Could not find post with id 1")

    def testUnsupportedAcceptHeader(self):
        response = self.client.get("/api/posts", headers=[("Accept", "application/xml")])

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Request must accept application/json data")  

    def testGetPostsWithTitleAndBody(self):
        """ Filtering posts by title """
        postA = models.Post(title="Post with bells", body="Just a test with bells")
        postB = models.Post(title="Post with whistles", body="Still a test with whistles")
        postC = models.Post(title="Post with bells and whistles", body="Another test with bells and whistles")

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=whistles&body_like=bells", headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 1)
        
        post = posts[0]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "Another test with bells and whistles")    

    def testPostPost(self):
        """ Posting a new post """
        data = {
            "title": "Example Post",
            "body": "Just a test"
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/posts/1")

        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Example Post")
        self.assertEqual(data["body"], "Just a test")

        posts = session.query(models.Post).all()
        self.assertEqual(len(posts), 1)

        post = posts[0]
        self.assertEqual(post.title, "Example Post")
        self.assertEqual(post.body, "Just a test")

    def testUnsupportedMimetype(self):
        data = "<xml></xml>"
        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/xml",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Request must contain application/json data")
        
    def testInvalidData(self):
        """ Posting a post with an invalid body """
        data = {
            "title": "Example Post",
            "body": 32
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "32 is not of type 'string'")

    def testMissingData(self):
        """ Posting a post with a missing body """
        data = {
            "title": "Example Post",
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "'body' is a required property")
        
if __name__ == "__main__":
    unittest.main()
