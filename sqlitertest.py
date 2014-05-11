import sqliter
import unittest
import threading

class  ModelTest(unittest.TestCase):
    """docstring for  ModelTest"""
    
    def setUp(self):
        class User(sqliter.Model):
            __tablename__ = "users"
            name = sqliter.Field("name", "varchar(50)")
            email = sqliter.Field("email", "varchar(20)", validator=lambda x: 7 < len(x) < 21)
    
        sqliter.setup_database('conf/test.sqlite')
        sqliter.bind_mapper('UserMapper', User)
        sqliter.UserMapper.create_table()
        self.user = User(name='test', email='test@example.com')

    def tearDown(self):
        res = sqliter.UserMapper.deleteby(name=self.user.name, email=self.user.email)
        #sqliter.UserMapper.drop_table()
        self.assertEqual(True, res)

    def test_model_save(self):
        self.assertEqual(True, self.user.save())

    def test_mapper_save(self):
        self.assertEqual(True, sqliter.UserMapper.save(self.user))

    def test_in_threads(self):
        n = 5
        ts = []
        for i in range(n):
            t = threading.Thread(target=self.user.save)
            ts.append(t)
        for t in ts:
            t.start()
        for t in ts:
            t.join()


if __name__ == "__main__":
    unittest.main()



    