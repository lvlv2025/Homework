# ==============================
# 1. 标准库导入
# ==============================
import os
import io
import yaml
import logging
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from functools import wraps

# ==============================
# 2. 第三方库导入
# ==============================
from flask import Flask, request, session, jsonify, send_file
from flask_cors import CORS
from flask_restx import Api, fields, Resource
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.jose import jwt

# ==============================
# 3. 自定义模块导入
# ==============================
from jwt_setting import generate_token, verify_token
from creat_id import generate_unique_user_uuid, generate_topic_id
from db_model import Base, Users_info, ChatHistory, Admin_info
from captcha import generate_math_captcha
from ai_chat import get_chat_data


# ==============================
# 数据库与应用初始化
# ==============================
# 读取数据库配置
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
db_conf = config['database']

# 创建数据库引擎
engine = create_engine(
    f"{db_conf['type']}://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database_name']}?charset={db_conf['charset']}",
    echo=False
)

# 创建数据库表
Base.metadata.create_all(engine)
# 创建数据库会话
Session_sql = sessionmaker(bind=engine)


# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'manlimanlimanli'  # 保留原始密钥
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
CORS(app, supports_credentials=True)


# ==============================
# Swagger文档配置（无Default命名空间）
# ==============================
api = Api(
    app,
    version='1.0',
    title='聊天系统API文档',
    description='聊天系统后端接口的详细说明和测试工具',
    doc='/api/docs/',
    prefix='',
    security_definitions={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': '请输入格式为 "Bearer {token}" 的认证令牌'
        }
    }
)

# 1. 验证码专用命名空间
auth_ns = api.namespace(
    'auth', 
    path='/api',  
    description='认证相关验证码接口',
    ordered=True
)

# 2. 用户操作命名空间（登录/注册）
user_ops_ns = api.namespace(
    'user-operations', 
    path='/api',  
    description='用户登录注册相关接口',
    ordered=True
)

# 3. 其他命名空间
chat_ns = api.namespace(
    'chat', 
    path='/api/chat',  
    description='聊天相关接口', 
    security='Bearer'
)
user_ns = api.namespace(
    'users', 
    path='/api/users',  
    description='用户信息管理接口', 
    security='Bearer'
)
admin_ns = api.namespace(
    'admin', 
    path='/api/admin',  
    description='管理员相关接口', 
    security='Bearer'
)


# ==============================
# 数据模型定义（按命名空间分类）
# ==============================
# 2.1 用户操作相关模型
login_model = user_ops_ns.model('LoginRequest', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码'),
    'captcha': fields.String(required=True, description='验证码')
})

register_model = user_ops_ns.model('RegisterRequest', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码（至少6位）'),
    'email': fields.String(required=True, description='邮箱'),
    'captcha': fields.String(required=True, description='验证码')
})

# 3.1 聊天相关模型
chat_request_model = chat_ns.model('ChatRequest', {
    'text': fields.String(required=True, description='用户提问内容'),
    'topic_id': fields.String(required=False, description='对话主题ID（新对话可不传）')
})

# 4.1 管理员相关模型
admin_login_model = admin_ns.model('AdminLoginRequest', {
    'admin_name': fields.String(required=True, description='管理员用户名'),
    'password': fields.String(required=True, description='管理员密码')
})

create_admin_model = admin_ns.model('CreateAdminRequest', {
    'admin_name': fields.String(required=True, description='新管理员用户名'),
    'password': fields.String(required=True, description='新管理员密码')
})


# ==============================
# 日志配置
# ==============================
if not os.path.exists('logs'):
    os.mkdir('logs')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
)
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=1024 * 1024 * 5,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.info('Flask应用启动，日志系统初始化完成')


# ==============================
# 登录验证装饰器
# ==============================
def login_required(role='user'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"success": False, "message": "缺少或无效的Token"}), 401

            token = auth_header.split(" ")[1]
            claims = verify_token(token, app.secret_key)
            if not claims:
                return jsonify({"success": False, "message": "Token无效或已过期"}), 401

            # 角色校验
            if role == 'user' and 'user_uuid' not in claims:
                return jsonify({"success": False, "message": "无效的用户凭证"}), 403
            if role == 'admin' and 'admin_name' not in claims:
                return jsonify({"success": False, "message": "无效的管理员凭证"}), 403

            # 将claims传递给视图函数
            kwargs['claims'] = claims
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==============================
# 1. 验证码接口（auth_ns）
# ==============================

# 1.1 登录验证码
@auth_ns.route('/login/captcha')  
class LoginCaptchaResource(Resource):
    @api.doc(
        description='获取登录验证码图片（支持?t=时间戳防缓存）',
        responses={200: '返回验证码图片', 500: '生成失败'},
        tags=['认证相关']
    )
    def get(self):
        try:
            img, captcha_text = generate_math_captcha()
            session['captcha_text'] = captcha_text
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            response = send_file(buf, mimetype='image/png')
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            return response
        except Exception as e:
            app.logger.error(f"生成登录验证码失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "验证码生成失败"}), 500


# 1.2 注册验证码
@auth_ns.route('/register/captcha')  
class RegisterCaptchaResource(Resource):
    @api.doc(
        description='获取注册验证码图片（支持?t=时间戳防缓存）',
        responses={200: '返回验证码图片', 500: '生成失败'},
        tags=['认证相关']
    )
    def get(self):
        try:
            img, captcha_text = generate_math_captcha()
            session['captcha_text'] = captcha_text
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            response = send_file(buf, mimetype='image/png')
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            return response
        except Exception as e:
            app.logger.error(f"生成注册验证码失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "验证码生成失败"}), 500


# ==============================
# 2. 用户操作接口（user_ops_ns）
# ==============================

# 2.1 用户登录
@user_ops_ns.route('/login')
class LoginResource(Resource):
    @api.doc(
        description='用户登录接口',
        responses={200: '登录成功', 400: '验证码错误/参数缺失', 401: '用户名/密码错误', 500: '服务器错误'},
        tags=['用户操作']
    )
    @user_ops_ns.expect(login_model)
    def post(self):
        data = request.json
        username = data.get('username')
        input_password = data.get('password')
        captcha_input = data.get('captcha')

        # 验证码校验
        if 'captcha_text' not in session:
            return jsonify({"success": False, "message": "验证码已过期，请刷新"}), 400
        if captcha_input.lower() != session['captcha_text'].lower():
            return jsonify({"success": False, "message": "验证码错误"}), 400

        db_session = Session_sql()
        try:
            user = db_session.query(Users_info).filter_by(name=username).first()
            if not user or not check_password_hash(user.password, input_password):
                return jsonify({"success": False, "message": "用户名或密码错误"}), 401

            # 生成JWT
            token = generate_token(
                {'user_uuid': user.user_uuid, 'username': user.name},
                app.secret_key,
                expires_in=3600
            )
            return jsonify({
                "success": True,
                "message": "登录成功",
                "username": user.name,
                "token": token
            })
        except Exception as e:
            app.logger.error(f"用户登录失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "登录失败，请稍后重试"}), 500
        finally:
            db_session.close()


# 2.2 用户注册
@user_ops_ns.route('/register')
class RegisterResource(Resource):
    @api.doc(
        description='用户注册接口',
        responses={200: '注册成功', 400: '参数错误/用户名/邮箱已存在', 500: '服务器错误'},
        tags=['用户操作']
    )
    @user_ops_ns.expect(register_model)
    def post(self):
        data = request.json
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        captcha = data.get("captcha")

        # 验证码校验
        if 'captcha_text' not in session or not captcha or captcha.lower() != session['captcha_text'].lower():
            return jsonify({"success": False, "message": "验证码错误"}), 400
        session.pop('captcha_text', None)  # 防止重复使用

        # 基础参数校验
        if not username or not password or not email:
            return jsonify({"success": False, "message": "用户名、密码和邮箱不能为空"}), 400
        if len(password) < 6:
            return jsonify({"success": False, "message": "密码至少需要6位"}), 400

        hashed_password = generate_password_hash(password)
        try:
            with Session_sql() as db_session:
                user_uuid = generate_unique_user_uuid(db_session)
                user = Users_info(
                    name=username,
                    password=hashed_password,
                    email=email,
                    user_uuid=user_uuid
                )
                db_session.add(user)
                db_session.commit()
                return jsonify({
                    "success": True,
                    "message": "注册成功",
                    "user_uuid": user_uuid
                }), 200
        except IntegrityError as e:
            db_session.rollback()
            err_msg = str(e.orig).lower()
            if "name" in err_msg:
                return jsonify({"success": False, "message": "用户名已存在"}), 400
            elif "email" in err_msg:
                return jsonify({"success": False, "message": "邮箱已存在"}), 400
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"注册用户失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "注册失败，请稍后重试"}), 500


# ==============================
# 3. 聊天相关接口（chat_ns）
# ==============================

# 3.1 发送聊天消息
@chat_ns.route('')  # 完整路径：/api/chat
class ChatResource(Resource):
    @api.doc(
        description='发送聊天消息获取AI回复',
        responses={200: '返回AI回复', 401: '未认证/Token无效', 500: '服务器错误'}
    )
    @chat_ns.expect(chat_request_model)
    @login_required(role='user')
    def post(self, claims):
        data = request.json
        user_message = data.get("text", "")
        topic_id = data.get("topic_id")
        user_uuid = claims['user_uuid']

        with Session_sql() as db_session:
            # 生成新topic_id（无则创建）
            if not topic_id:
                topic_id = generate_topic_id(db_session, user_uuid)

            # 查询历史聊天记录
            history_records = (
                db_session.query(ChatHistory)
                .filter_by(user_uuid=user_uuid, topic_id=topic_id)
                .order_by(asc(ChatHistory.id))
                .all()
            )

        # 构建对话历史
        chat_history = [{"role": "system", "content": "你是一个有用的助手"}]
        for record in history_records:
            chat_history.append({"role": "user", "content": record.question})
            chat_history.append({"role": "assistant", "content": record.answer})

        # 获取AI回复并保存记录
        chat_history.append({"role": "user", "content": user_message})
        response_message = get_chat_data(chat_history)
        chat_record = ChatHistory(
            user_uuid=user_uuid,
            topic_id=topic_id,
            question=user_message,
            answer=response_message
        )

        try:
            with Session_sql() as db_session:
                db_session.add(chat_record)
                db_session.commit()
            return jsonify({
                "success": True,
                "reply": response_message,
                "topic_id": topic_id
            })
        except Exception as e:
            app.logger.error(f"保存聊天记录失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "error": "保存失败，请稍后重试"}), 500


# 3.2 开启新聊天话题
@chat_ns.route('/update_chat')  # 完整路径：/api/chat/update_chat
class UpdateChatResource(Resource):
    @api.doc(
        description='开启新聊天话题',
        responses={200: '返回新topic_id', 400: '参数缺失', 401: '未认证/Token无效'}
    )
    @login_required(role='user')
    def post(self, claims):
        data = request.get_json()
        if data.get("new"):
            user_uuid = claims['user_uuid']
            with Session_sql() as db_session:
                topic_id = generate_topic_id(db_session, user_uuid)
            return jsonify({
                "success": True,
                "message": "新话题已开始",
                "topic_id": topic_id,
                "chat_history": [{"role": "system", "content": "You are a helpful assistant"}]
            })
        return jsonify({"success": False, "message": "参数缺失"}), 400


# 3.3 获取聊天历史列表（分页）
@chat_ns.route('/history')  # 完整路径：/api/chat/history
class ChatHistoryResource(Resource):
    @api.doc(
        description='获取用户所有聊天历史列表（分页）',
        params={'page': '页码（默认1）', 'size': '每页数量（默认10）'},
        responses={200: '返回历史列表', 401: '未认证/Token无效', 404: '无历史记录'}
    )
    @login_required(role='user')
    def get(self, claims):
        user_uuid = claims['user_uuid']
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))

        db_session = Session_sql()
        try:
            # 查询所有topic_id（去重）
            topic_ids = db_session.query(ChatHistory.topic_id).filter_by(user_uuid=user_uuid).distinct().all()
            if not topic_ids:
                return jsonify({"error": "未找到记录"}), 404

            # 分页处理
            start = (page - 1) * size
            end = start + size
            paginated_topics = [topic[0] for topic in topic_ids[start:end]]  # 提取topic_id

            # 构建历史列表（取每个话题的第一条消息作为标题）
            history_list = []
            for topic_id in paginated_topics:
                first_msg = db_session.query(ChatHistory).filter_by(
                    user_uuid=user_uuid, topic_id=topic_id
                ).order_by(asc(ChatHistory.id)).first()
                
                if first_msg:
                    history_list.append({
                        "topic_id": topic_id,
                        "first_message": first_msg.question
                    })

            return jsonify({
                "success": True,
                "total": len(topic_ids),
                "page": page,
                "size": size,
                "history": history_list
            })
        except Exception as e:
            app.logger.error(f"获取聊天历史列表失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "error": "获取失败，请稍后重试"}), 500
        finally:
            db_session.close()


# 3.4 获取特定话题的聊天详情
@chat_ns.route('/history/<string:topic_id>')  # 完整路径：/api/chat/history/{topic_id}
class SpecificChatHistoryResource(Resource):
    @api.doc(
        description='获取特定话题的完整聊天记录',
        responses={200: '返回详细记录', 401: '未认证', 404: '话题不存在'}
    )
    @login_required(role='user')
    def get(self, topic_id, claims):
        user_uuid = claims['user_uuid']
        db_session = Session_sql()
        try:
            # 验证话题是否属于当前用户
            records = db_session.query(ChatHistory).filter_by(
                user_uuid=user_uuid, topic_id=topic_id
            ).order_by(asc(ChatHistory.id)).all()
            
            if not records:
                return jsonify({"error": "话题不存在或无权限访问"}), 404

            # 构建详细聊天记录
            chat_details = []
            for record in records:
                chat_details.append({
                    "id": record.id,
                    "user_message": record.question,
                    "ai_reply": record.answer
                })

            return jsonify({
                "success": True,
                "topic_id": topic_id,
                "chat_details": chat_details
            })
        except Exception as e:
            app.logger.error(f"获取特定话题聊天记录失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "error": "获取失败，请稍后重试"}), 500
        finally:
            db_session.close()


# 3.5 删除特定话题的聊天记录
@chat_ns.route('/history/<string:topic_id>', methods=['DELETE'])
class DeleteChatHistoryResource(Resource):
    @api.doc(
        description='删除特定话题的所有聊天记录',
        responses={200: '删除成功', 401: '未认证', 404: '话题不存在', 500: '删除失败'}
    )
    @login_required(role='user')
    def delete(self, topic_id, claims):
        user_uuid = claims['user_uuid']
        db_session = Session_sql()
        try:
            # 验证话题是否属于当前用户
            records = db_session.query(ChatHistory).filter_by(
                user_uuid=user_uuid, topic_id=topic_id
            ).all()
            
            if not records:
                db_session.close()
                return {
                    "success": False, 
                    "message": "话题不存在或无权限访问"
                }, 404

            # 删除该话题的所有记录
            for record in records:
                db_session.delete(record)
            db_session.commit()
            
            return {
                "success": True, 
                "message": f"话题 {topic_id} 的记录已成功删除",
                "topic_id": topic_id
            }, 200

        except Exception as e:
            db_session.rollback()
            app.logger.error(f"删除聊天记录失败: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "删除失败，请稍后重试"
            }, 500

        finally:
            db_session.close()


# ==============================
# 4. 用户信息管理接口（user_ns）
# ==============================

# 4.1 获取用户信息
@user_ns.route('/info')
class UserInfoResource(Resource):
    @api.doc(
        description='获取当前登录用户信息',
        responses={200: '返回用户信息', 401: '未认证/Token无效'}
    )
    @login_required(role='user')
    def get(self, claims):
        user_uuid = claims['user_uuid']
        db_session = Session_sql()
        try:
            user = db_session.query(Users_info).filter_by(user_uuid=user_uuid).first()
            if not user:
                return jsonify({"success": False, "message": "用户不存在"}), 404

            return jsonify({
                "success": True,
                "user_info": {
                    "username": user.name,
                    "email": user.email,
                    "user_uuid": user.user_uuid,
                    "register_time": user.register_time
                }
            })
        except Exception as e:
            app.logger.error(f"获取用户信息失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "获取信息失败，请稍后重试"}), 500
        finally:
            db_session.close()


# 4.2 修改密码
@user_ns.route('/update_password')
class UpdatePasswordResource(Resource):
    @api.doc(
        description='修改用户密码',
        responses={200: '修改成功', 400: '参数错误', 401: '未认证', 500: '服务器错误'}
    )
    @login_required(role='user')
    def post(self, claims):
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        user_uuid = claims['user_uuid']

        if not old_password or not new_password:
            return jsonify({"success": False, "message": "旧密码和新密码不能为空"}), 400
        if len(new_password) < 6:
            return jsonify({"success": False, "message": "新密码至少需要6位"}), 400

        db_session = Session_sql()
        try:
            user = db_session.query(Users_info).filter_by(user_uuid=user_uuid).first()
            if not user or not check_password_hash(user.password, old_password):
                return jsonify({"success": False, "message": "旧密码错误"}), 400

            # 更新密码
            user.password = generate_password_hash(new_password)
            db_session.commit()
            return jsonify({"success": True, "message": "密码修改成功"}), 200
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"修改密码失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "修改失败，请稍后重试"}), 500
        finally:
            db_session.close()


# ==============================
# 5. 管理员接口（admin_ns）
# ==============================

# 5.1 管理员登录
@admin_ns.route('/login')
class AdminLoginResource(Resource):
    @api.doc(
        description='管理员登录接口',
        responses={200: '登录成功', 401: '用户名/密码错误', 500: '服务器错误'}
    )
    @admin_ns.expect(admin_login_model)
    def post(self):
        data = request.json
        admin_name = data.get('admin_name')
        password = data.get('password')

        db_session = Session_sql()
        try:
            admin = db_session.query(Admin_info).filter_by(admin_name=admin_name).first()
            if not admin or not check_password_hash(admin.password, password):
                return jsonify({"success": False, "message": "管理员用户名或密码错误"}), 401

            # 生成管理员JWT
            token = generate_token(
                {'admin_name': admin.admin_name},
                app.secret_key,
                expires_in=3600
            )
            return jsonify({
                "success": True,
                "message": "管理员登录成功",
                "admin_name": admin.admin_name,
                "token": token
            })
        except Exception as e:
            app.logger.error(f"管理员登录失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "登录失败，请稍后重试"}), 500
        finally:
            db_session.close()


# 5.2 创建新管理员
@admin_ns.route('/create')
class CreateAdminResource(Resource):
    @api.doc(
        description='创建新管理员（仅超级管理员可用）',
        responses={200: '创建成功', 400: '参数错误/管理员已存在', 403: '无权限', 500: '服务器错误'}
    )
    @admin_ns.expect(create_admin_model)
    @login_required(role='admin')
    def post(self, claims):
        # 假设只有名为"superadmin"的管理员可创建新管理员
        if claims['admin_name'] != 'superadmin':
            return jsonify({"success": False, "message": "无权限创建新管理员"}), 403

        data = request.json
        admin_name = data.get('admin_name')
        password = data.get('password')

        if not admin_name or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
        if len(password) < 6:
            return jsonify({"success": False, "message": "密码至少需要6位"}), 400

        hashed_password = generate_password_hash(password)
        try:
            with Session_sql() as db_session:
                # 检查管理员是否已存在
                if db_session.query(Admin_info).filter_by(admin_name=admin_name).first():
                    return jsonify({"success": False, "message": "管理员已存在"}), 400

                new_admin = Admin_info(
                    admin_name=admin_name,
                    password=hashed_password
                )
                db_session.add(new_admin)
                db_session.commit()
                return jsonify({"success": True, "message": "新管理员创建成功"}), 200
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"创建管理员失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "创建失败，请稍后重试"}), 500


# 5.3 获取用户列表
@admin_ns.route('/users')
class AdminUserListResource(Resource):
    @api.doc(
        description='获取所有用户列表（分页）',
        params={'page': '页码（默认1）', 'size': '每页数量（默认20）'},
        responses={200: '返回用户列表', 401: '未认证', 403: '无权限', 500: '服务器错误'}
    )
    @login_required(role='admin')
    def get(self, claims):
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        start = (page - 1) * size

        db_session = Session_sql()
        try:
            # 查询总用户数
            total_users = db_session.query(Users_info).count()
            # 分页查询用户
            users = db_session.query(Users_info).order_by(Users_info.register_time.desc()).offset(start).limit(size).all()

            user_list = []
            for user in users:
                user_list.append({
                    "user_uuid": user.user_uuid,
                    "username": user.name,
                    "email": user.email,
                    "register_time": user.register_time
                })

            return jsonify({
                "success": True,
                "total": total_users,
                "page": page,
                "size": size,
                "users": user_list
            })
        except Exception as e:
            app.logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": "获取失败，请稍后重试"}), 500
        finally:
            db_session.close()


# ==============================
# 应用启动入口
# ==============================
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True  # 生产环境需改为False
    )
    