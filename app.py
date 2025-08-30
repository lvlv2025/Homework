from flask import Flask,render_template,request,redirect,url_for,make_response,session,flash,jsonify
from captcha import generate_captcha,generate_math_captcha
import io
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_model import Base, Users_info
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
from ai_chat import get_chat_data


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

def login_required(f):
    @wraps(f)  # 保留原函数的元信息
    def decorated_function(*args, **kwargs):
        # 检查session中是否有user_id
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))  # 跳转到登录页
        return f(*args, **kwargs)  # 如果已登录，执行原函数
    return decorated_function


@app.route("/login" , methods=['POST','GET'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        input_password = request.form.get('password')
        user = session_sql.query(Users_info).filter_by(name=username).first()
        remember = request.form.get('remember', 'off')  # 如果没有remember字段，默认为'no'

        if user and check_password_hash(user.password, input_password):
            if 'captcha_text' not in session:
                return render_template("login.html", alert_message="验证码已过期，请刷新")


            if 'captcha_text' in session and request.form['captcha'].lower() == session['captcha_text'].lower():
                # 设置会话
                session['user_id'] = user.id
                session['username'] = user.name

                # 根据"记住我"选项设置会话有效期
                session.permanent = (remember == 'on')  # True=长期会话，False=浏览器关闭后失效
                return redirect(url_for('chat'))
            else:
                return render_template("login.html", alert_message="验证码错误")
        else:
            # 登录失败
            return render_template("login.html", alert_message="用户名或密码错误")

    else:
        return render_template("login.html")

@app.route("/register" , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")

    else:

        if 'captcha_text' in session and request.form['captcha'].lower() == session['captcha_text'].lower():
            # 验证成功后清除session中的验证码（防止重复使用）
            session.pop('captcha_text', None)

            # 安全方式加密密码（默认方法是pbkdf2:sha256）
            hashed_password = generate_password_hash(request.form['password'])


            session_sql.add(
                Users_info(
                    name=request.form['username'],
                    password=hashed_password,
                    email=request.form['email']
                )
            )
            session_sql.commit()
            return redirect(url_for('login'))
        else:
            # 验证失败时返回注册页，可以添加错误提示
            return render_template("register.html", alert_message="验证码错误")

@app.route("/login/captcha" , methods=['GET'])
def get_captcha():
    # 假设 captcha_mian() 生成验证码并返回 PIL 图像对象
    img, captcha_text = generate_math_captcha()  # 需返回 PIL.Image 对象

    # 将验证码文本存入session
    session['captcha_text'] = captcha_text

    print(captcha_text)
    # 将图像转为二进制响应
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    response = make_response(img_bytes.read())
    response.headers['Content-Type'] = 'image/png'
    return response

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

@app.route("/")
def test():
    return redirect('/login')
    #return '/login'

chat_history = [
           {"role": "system", "content": "You are a helpful assistant"},
        ]

@app.route("/chat/get_response",methods=['POST'])
@login_required
def get_response():
    #if request.get_json('new')
    print(request.get_json())
    data = request.get_json()
    #print(data)
    user_message = data.get("text", "")

    chat_history.append({"role": "user", "content": user_message})

    response = get_chat_data(chat_history)

    chat_history.append({"role": "assistant", "content": response})

    return jsonify({"reply": response})

@app.route("/chat/update_chat", methods=['POST'])
@login_required
def update_chat():
    global chat_history
    if request.get_json().get("new"):
        chat_history = [
            {"role": "system", "content": "You are a helpful assistant"},
        ]
        return jsonify({"status": "ok", "message": "新话题已开始"})
    return jsonify({"status": "no-change"})

@app.route('/logout')
def logout():
    # 清除会话数据
    session.clear()
    # 确保客户端 Cookie 过期（可选）
    response = redirect(url_for('login'))
    response.delete_cookie('session')
    return response

if __name__ == '__main__':
    #db_conf = load_config()
    #connect_db(db_conf,'users')
    app.run(host='0.0.0.0')