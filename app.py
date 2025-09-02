from flask import Flask,render_template,request,redirect,url_for,make_response,session,flash,jsonify,send_file
from captcha import generate_captcha,generate_math_captcha
import io
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,Session
from db_model import Base, Users_info,ChatHistory
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
from ai_chat import get_chat_data
from flask_cors import CORS
import time, random


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
    f"{db_conf['type']}://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database_name']}?charset=utf8",
    echo=False
)

# 创建表（仅首次）
Base.metadata.create_all(engine)
# 创建会话
Session_sql = sessionmaker(bind=engine)
session_sql = Session_sql()

# 创建 Flask 应用
app = Flask(__name__)
app.secret_key = 'manlimanlimanli'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 设为 7 天
CORS(app, supports_credentials=True)  # 支持 cookie/session

def login_required(f):
    """
    登录验证，检查 session 中是否有 user_uuid
    如果未登录，返回 JSON 错误，前端处理跳转
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_uuid' not in session:
            # 未登录，返回 JSON
            return jsonify({
                "success": False,
                "message": "未登录，请先登录"
            }), 401  # 401 Unauthorized
        return f(*args, **kwargs)
    return decorated_function

@app.route("/api/login", methods=['POST'])    #如果是post请求，在数据库进行匹配
def login():

    data = request.json
    username = data.get('username')
    input_password = data.get('password')
    captcha_input = data.get('captcha')
    remember = data.get('remember', False)

    user = session_sql.query(Users_info).filter_by(name=username).first()

    if not user or not check_password_hash(user.password, input_password):
        return jsonify({"success": False, "message": "用户名或密码错误"}), 401

    if 'captcha_text' not in session:
        return jsonify({"success": False, "message": "验证码已过期，请刷新"}), 400

    if captcha_input.lower() != session['captcha_text'].lower():
        return jsonify({"success": False, "message": "验证码错误"}), 400

    session['user_uuid'] = user.user_uuid
    session['username'] = user.name
    session.permanent = bool(remember)

    return jsonify({"success": True, "message": "登录成功", "username": user.name})


@app.route("/api/register", methods=['POST'])
def register():
    data = request.json  # Vue 端 axios 默认传 JSON
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    captcha = data.get("captcha")

    # 验证码检查
    if 'captcha_text' not in session or captcha.lower() != session['captcha_text'].lower():
        return jsonify({"success": False, "message": "验证码错误"}), 400

    # 清除 session 里的验证码，防止重复使用
    session.pop('captcha_text', None)

    # 密码加密存储
    hashed_password = generate_password_hash(password)

    # 生成唯一 user_uuid
    user_uuid = generate_unique_user_uuid(session_sql)

    try:
        user = Users_info(
            name=username,
            password=hashed_password,
            email=email,
            user_uuid=user_uuid  # 新增字段
        )
        session_sql.add(user)
        session_sql.commit()
        return jsonify({
            "success": True,
            "message": "注册成功",
            "user_uuid": user_uuid  # 返回给前端
        })
    except Exception as e:
        session_sql.rollback()
        return jsonify({"success": False, "message": "数据库错误: " + str(e)}), 500


@app.route("/api/login/captcha", methods=['GET'])     #获得登录时的验证吗
def get_login_captcha():
    img, captcha_text = generate_math_captcha()
    session['captcha_text'] = captcha_text
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


chat_history = [
           {"role": "system", "content": "You are a helpful assistant"},
        ]

@app.route("/api/chat/get_response", methods=['POST'])
@login_required
def get_chat_response():
    data = request.get_json()
    user_message = data.get("text", "")
    topic_id = data.get("topic_id")  # 前端传递的 topic_id

    if not topic_id:
        topic_id = generate_topic_id()  # 第一次生成

    response = get_chat_data([{"role": "user", "content": user_message}])

    # 保存到数据库

    chat_record = ChatHistory(
        user_uuid=session['user_uuid'],
        topic_id=topic_id,
        question=user_message,
        answer=response
    )

    try:
        session_sql.add(chat_record)
        session_sql.commit()
    except Exception as e:
        session_sql.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        session_sql.close()

    return jsonify({"success": True, "reply": response, "topic_id": topic_id})


@app.route("/api/chat/update_chat", methods=['POST'])     #开启新话题
@login_required
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


@app.route("/api/chat/history_response",methods=['POST'])
@login_required
def get_chat_history_response():
    '''
    获得需要查询的用户UUID和会话的topic_id
    :return:
    '''
    user_uuid = request.get_json('user_uuid')
    topic_id = request.get_json('topic_id')

    #print(user_uuid, topic_id)
    if not user_uuid or not topic_id:
        return jsonify({"error": "缺少参数"}), 400

    # 查询数据库，返回多条记录
    chats = session_sql.query(ChatHistory).filter_by(user_uuid=user_uuid, topic_id=topic_id).all()

    if not chats:
        return jsonify({"error": "未找到记录"}), 404

    # 返回所有记录
    reply = []
    for chat in chats:
        reply.append({"role": "user", "content": chat.question})
        reply.append({"role": "assistant", "content": chat.answer})

    return jsonify({"reply": reply})


@app.route('/api/logout', methods=['POST'])
def logout():
    if 'user_uuid' not in session:   # 如果本来就没登录
        return jsonify({"success": False,"message": "未登录，无法登出"}), 400

    # 清除会话
    uuid = session['user_uuid']
    session.clear()
    return jsonify({"success": True,"message": "登出成功",'uuid':uuid}), 200

if __name__ == '__main__':
    #db_conf = load_config()
    #connect_db(db_conf,'users')
    app.run(host='0.0.0.0')