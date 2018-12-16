import sqlite3
from flask_restful import Resource
from flask_restful import reqparse
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token
from flask_jwt_extended import jwt_refresh_token_required
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_raw_jwt
from models.user import UserModel
from blacklist import BLACKLIST


class UserBase(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )
    parser.add_argument('password',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )


class UserRegister(UserBase):
    def post(self):
        data = UserRegister.parser.parse_args()

        username = data['username']
        if UserModel.find_by_username(username):
            return {"message": "A user already exists"}, 400

        user = UserModel(**data)
        user.save_to_db()

        return {"message": "User created successfully."}, 201


class User(Resource):
    @classmethod
    def get(cls, user_id):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': 'user not found'}, 404
        return user.json()

    @classmethod
    def delete(cls, user_id):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': 'user not found'}, 404
        user.delete_from_db()
        return {'message': 'User deleted'}, 200


class UserLogin(UserBase):
    @classmethod
    def post(cls):
        data = cls.parser.parse_args()
        username = data['username']
        password = data['password']
        user = UserModel.find_by_username(username)
        if user and user.password == password:
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200
        return {"message": "Invalid credential"}, 401


class UserLogout(UserBase):
    @jwt_required
    def get(self):
        # jti is JWT ID
        jti = get_raw_jwt()['jti']
        BLACKLIST.add(jti)
        return {
            'message': 'Successfully logged out'
        }, 200


class TokenRefresh(Resource):
   @jwt_refresh_token_required
   def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200
