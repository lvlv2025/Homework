from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash, jsonify, send_file
from captcha import generate_captcha, generate_math_captcha
import io
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db_model import Base, Users_info, ChatHistory ,Admin_info
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
from ai_chat import get_chat_data
from flask_cors import CORS
import time, random
import logging
from logging.handlers import RotatingFileHandler
import os



def generate_unique_user_uuid(db: Session, length: int = 11):
    """
    生成指定长度的唯一用户UUID数字字符串
    :param db: 数据库 Session
    :param length: UUID 数字长度，默认为 11
    :return: 唯一数字字符串
    """
    if length < 1:
        raise ValueError("长度必须大于0")

    while True:
        # 生成指定长度的数字UUID
        start = 10**(length - 1)
        end = 10**length - 1
        user_uuid = str(random.randint(start, end))

        # 查询数据库是否已存在
        exists = db.query(Users_info).filter_by(user_uuid=user_uuid).first()
        if not exists:
            return user_uuid

def generate_topic_id(length: int = 8):
    '''
    生成会话id
    :param length:
    :return:
    '''
    start = 10 ** (length - 1)
    end = 10 ** length - 1
    topic_id = str(random.randint(start, end))

    return topic_id


with open("config.yaml", "r", encoding="utf-8") as f:   #修改数据库模板名字
    config = yaml.safe_load(f)
db_conf = config['database']
# 创建数据库引擎
engine = create_engine(
    f"{db_conf['type']}://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database_name']}?charset={db_conf['charset']}",
    echo=False
)

# 创建表（仅首次）
Base.metadata.create_all(engine)
# 创建会话
Session_sql = sessionmaker(bind=engine)


# 创建 Flask 应用
app = Flask(__name__)
app.secret_key = 'manlimanlimanli'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 设为 7 天
CORS(app, supports_credentials=True)  # 支持 cookie/session


# 日志配置（用于排查接口调用、路由注册问题）
if not os.path.exists('logs'):
    os.mkdir('logs')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
)
# 文件日志（存到 logs/app.log，最大5MB，保留5个备份）
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=1024 * 1024 * 5,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)
# 绑定到 Flask 应用日志
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.info('Flask应用启动，日志系统初始化完成')



def login_required(role='user'):
    """
    登录验证
    role: 'user' 或 'admin'
    普通用户用 user_uuid，管理员用 admin_name
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if role == 'user':
                if 'user_uuid' not in session:
                    return jsonify({
                        "success": False,
                        "message": "未登录，请先登录用户账号"
                    }), 401
            elif role == 'admin':
                if 'admin_name' not in session:
                    return jsonify({
                        "success": False,
                        "message": "未登录，请先登录管理员账号"
                    }), 401
            else:
                return jsonify({
                    "success": False,
                    "message": "角色未定义"
                }), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route("/api/login", methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    input_password = data.get('password')
    captcha_input = data.get('captcha')
    remember = data.get('remember', False)

    # 先校验验证码
    if 'captcha_text' not in session:
        return jsonify({"success": False, "message": "验证码已过期，请刷新"}), 400
    if captcha_input.lower() != session['captcha_text'].lower():
        return jsonify({"success": False, "message": "验证码错误"}), 400

    db_session = Session_sql()
    try:
        user = db_session.query(Users_info).filter_by(name=username).first()
        if not user or not check_password_hash(user.password, input_password):
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401

        # 设置 session
        session['user_uuid'] = user.user_uuid
        session['username'] = user.name
        session.permanent = bool(remember)

        return jsonify({"success": True, "message": "登录成功", "username": user.name})
    except Exception as e:
        app.logger.error(f"用户登录失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "登录失败，请稍后重试"}), 500
    finally:
        db_session.close()


@app.route("/api/register", methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    captcha = data.get("captcha")

    # 验证码检查
    if 'captcha_text' not in session or captcha.lower() != session['captcha_text'].lower():
        return jsonify({"success": False, "message": "验证码错误"}), 400

    session.pop('captcha_text', None)  # 防止重复使用

    hashed_password = generate_password_hash(password)
    db_session = Session_sql()
    user_uuid = generate_unique_user_uuid(db_session)

    try:
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
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"注册用户失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "注册失败，请稍后重试"}), 500
    finally:
        db_session.close()

@app.route("/api/login/captcha", methods=['GET'])     #获得登录时的验证吗
def get_login_captcha():
    img, captcha_text = generate_math_captcha()
    session['captcha_text'] = captcha_text
    print(captcha_text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route("/api/register/captcha", methods=['GET'])     #获得注册时的验证吗
def get_register_captcha():
    img, captcha_text = generate_math_captcha()
    session['captcha_text'] = captcha_text
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# 聊天对话相关全局变量
chat_history = [
           {"role": "system", "content": "You are a helpful assistant"},
        ]

@app.route("/api/chat/get_response", methods=['POST'])
@login_required(role='user')
def get_chat_response():
    '''
    获得用户的提问，并发送回答
    :return:
    '''
    data = request.json
    user_message = data.get("text", "")
    topic_id = data.get("topic_id")  # 前端传递的 topic_id

    if not topic_id:
        topic_id = generate_topic_id()  # 第一次生成

    chat_history.append({"role": "user", "content": user_message})
    response_message = get_chat_data(chat_history)
    chat_history.append({"role": "assistant", "content": response_message})

    # 保存到数据库

    chat_record = ChatHistory(
        user_uuid=session['user_uuid'],
        topic_id=topic_id,
        question=user_message,
        answer=response_message
    )

    db_session = Session_sql()  # 每次请求创建新的Session
    try:
        db_session.add(chat_record)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"保存聊天记录失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "保存失败，请稍后重试"}), 500
    finally:
        db_session.close()  # 关闭Session
    return jsonify({"success": True, "reply": response_message, "topic_id": topic_id})


@app.route("/api/chat/update_chat", methods=['POST'])     #开启新话题
@login_required(role='user')
def update_chat():
    '''
    当前端开启新话题时，应传输一个参数 new=TRUE
    :return:
    '''
    global chat_history

    if request.get_json().get("new"):
        topic_id = generate_topic_id()  # 生成新的topic_id
        chat_history = [
            {"role": "system", "content": "You are a helpful assistant"},
        ]
        return jsonify({"success": True, "message": "新话题已开始","topic_id": topic_id})
    return jsonify({"success": False})


@app.route("/api/chat/history_response", methods=['POST'])
@login_required(role='user')
def get_chat_history_response():
    data = request.json
    user_uuid = data.get('user_uuid')
    topic_id = data.get('topic_id')

    if not user_uuid or not topic_id:
        return jsonify({"error": "缺少参数"}), 400

    db_session = Session_sql()
    try:
        chats = db_session.query(ChatHistory).filter_by(user_uuid=user_uuid, topic_id=topic_id).all()
        if not chats:
            return jsonify({"error": "未找到记录"}), 404

        reply = []
        for chat in chats:
            reply.append({"role": "user", "content": chat.question})
            reply.append({"role": "assistant", "content": chat.answer})

        return jsonify({"reply": reply})
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"查询聊天记录失败: {str(e)}", exc_info=True)
        return jsonify({"error": "查询失败，请稍后重试"}), 500
    finally:
        db_session.close()


# 新增加路由：个人信息查询接口
@app.route("/api/get_info/user", methods=['POST'])
@login_required(role='user')
def get_current_user_info():
    app.logger.debug('进入 /api/get_info/user 接口')
    current_user_uuid = session.get_json('user_uuid')
    app.logger.debug(f'从session获取user_uuid: {current_user_uuid}')

    db_session = Session_sql()
    try:
        app.logger.debug(f'开始查询用户信息，user_uuid: {current_user_uuid}')
        user = db_session.query(Users_info).filter_by(user_uuid=current_user_uuid).first()

        if not user:
            app.logger.warning(f'用户不存在，user_uuid: {current_user_uuid}')
            return jsonify({
                "success": False,
                "message": "用户不存在（可能已被删除）"
            }), 404

        app.logger.debug(f'查询到用户信息: {user.name}（{user.user_uuid}）')
        user_data = {
            "user_id": user.user_uuid,
            "username": user.name,
            "email": user.email
        }
        return jsonify({
            "success": True,
            "message": "用户信息查询成功",
            "data": user_data
        }), 200

    except Exception as e:
        app.logger.error(f'查询用户信息失败: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "message": "查询失败，请稍后重试"
        }), 500

    finally:
        db_session.close()
        app.logger.debug('数据库会话已关闭')



@app.route("/api/login/admin", methods=['POST'])
def admin_login():
    data = request.json
    admin_name = data.get('Admin_name')
    admin_password = data.get('password')

    if not admin_name or not admin_password:
        return jsonify({"success": False, "message": "缺少用户名或密码"}), 400

    db_session = Session_sql()
    try:
        admin = db_session.query(Admin_info).filter_by(name=admin_name).first()
        if not admin or not check_password_hash(admin.password, admin_password):
            return jsonify({"success": False, "message": "管理员名或密码错误"}), 401

        session['admin_name'] = admin_name
        return jsonify({"success": True, "message": "管理员登录成功", "admin_name": admin_name})
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"管理员登录失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "登录失败，请稍后重试"}), 500
    finally:
        db_session.close()


@app.route('/api/creat_info/admin', methods=['POST'])
@login_required('admin')
def creat_admin():
    data = request.json
    admin_name = data.get("username")
    admin_password = data.get("password")

    if not admin_name or not admin_password:
        return jsonify({"success": False, "message": "缺少用户名或密码"}), 400

    hashed_password = generate_password_hash(admin_password)
    db_session = Session_sql()

    try:
        admin = Admin_info(
            name=admin_name,
            password=hashed_password
        )
        db_session.add(admin)
        db_session.commit()
        return jsonify({
            "success": True,
            "message": "管理员注册成功",
            "admin_name": admin_name
        })
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"创建管理员失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "数据库错误，请稍后重试"}), 500
    finally:
        db_session.close()



@app.route('/api/get_info/admin', methods=['POST'])
@login_required('admin')
def get_admin_info():
    data = request.json
    admin_name = data.get("Admin_name")

    if not admin_name:
        return jsonify({"success": False, "message": "缺少管理员名"}), 400

    db_session = Session_sql()
    try:
        admin = db_session.query(Admin_info).filter_by(name=admin_name).first()
        if admin:
            # 不返回密码，只返回基本信息
            return jsonify({
                "success": True,
                "message": "查询成功",
                "Admin_name": admin_name
            }), 200
        else:
            return jsonify({"success": False, "message": "管理员不存在"}), 404
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"查询管理员信息失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "查询失败，请稍后重试"}), 500
    finally:
        db_session.close()



@app.route('/api/logout', methods=['POST'])
def logout():
    if 'user_uuid' not in session:   # 如果本来就没登录
        return jsonify({"success": False,"message": "未登录，无法登出"}), 400

    # 清除会话
    uuid = session['user_uuid']
    session.clear()
    return jsonify({"success": True,"message": "登出成功",'uuid':uuid}), 200


# 应用启动入口
if __name__ == '__main__':
    # 启动时打印所有已注册的路由
    with app.app_context():
        for rule in app.url_map.iter_rules():
            app.logger.info(f'已注册路由: {rule.methods} {rule.rule}')
    app.run(debug=True, host="0.0.0.0", port=5000)