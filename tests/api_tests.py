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
        
if __name__ == "__main__":
    unittest.main()
