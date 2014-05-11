Simple SQLite ORM
===================================


        class User(sqliter.Model):
            __tablename__ = "users"
            name = sqliter.Field("name", "varchar(50)")
            email = sqliter.Field("email", "varchar(20)", validator=lambda x: 7 < len(x) < 21)
    
        sqliter.setup_database('conf/test.sqlite')
        sqliter.bind_mapper('UserMapper', User)
        sqliter.UserMapper.create_table()
        user = User(name='test', email='test@example.com')
        user.save()
        sqliter.UserMapper.deleteby(name=user.name, email=user.email)