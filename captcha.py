
import string
import os
import random
from PIL import Image, ImageDraw, ImageFont


def generate_math_captcha():
    # 保持原始验证码尺寸
    width, height = 150, 44

    # 创建新图片
    image = Image.new('RGB', (width, height), color=(249, 249, 249))
    draw = ImageDraw.Draw(image)

    # 生成100以内的加减验证码（确保减法结果为正）
    num1 = random.randint(10, 99)
    num2 = random.randint(10, 99) if random.choice([True, False]) else random.randint(1, num1)
    operator = random.choice(['+', '-'])

    if operator == '-':
        num1, num2 = max(num1, num2), min(num1, num2)

    captcha_text = f"{num1}{operator}{num2}=?"
    correct_answer = str(num1 + num2) if operator == '+' else str(num1 - num2)

    # 使用更紧凑的字体
    try:
        font = ImageFont.truetype("arial.ttf", 20)  # 缩小字体大小以适应
    except:
        font = ImageFont.load_default()
        font.size = 20  # 尝试调整默认字体大小

    # 绘制验证码文本（更紧凑的布局）
    x_offset = 5
    for i, char in enumerate(captcha_text):
        # 随机颜色
        text_color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )

        # 更小的随机偏移
        x = x_offset + random.randint(-2, 2)
        y = 12 + random.randint(-3, 3)
        angle = random.randint(-10, 10)

        # 创建字符图像并旋转
        char_image = Image.new('RGBA', (15, 25), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((0, 0), char, fill=text_color, font=font)
        char_image = char_image.rotate(angle, expand=1)

        # 将旋转后的字符粘贴到主图像
        image.paste(char_image, (int(x), int(y)), char_image)
        x_offset += 13 if char.isdigit() else 8  # 数字更宽，符号更窄

    # 添加少量干扰线（减少数量以适应小尺寸）
    for _ in range(3):
        line_color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )
        start = (random.randint(0, width // 2), random.randint(0, height))
        end = (random.randint(width // 2, width), random.randint(0, height))
        draw.line([start, end], fill=line_color, width=1)

    # 添加适量噪点
    for _ in range(30):  # 减少噪点数量
        noise_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=noise_color)

    return image, correct_answer


def generate_captcha():
    # 验证码尺寸
    width, height = 150, 44

    # 创建新图片
    image = Image.new('RGB', (width, height), color=(249, 249, 249))
    draw = ImageDraw.Draw(image)

    # 生成4位随机验证码（字母和数字）
    captcha_text = ''.join(random.choices(
        string.ascii_letters + string.digits,
        k=4
    ))

    # 加载字体（使用默认字体或指定字体文件）
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    # 绘制验证码文本
    for i, char in enumerate(captcha_text):
        # 随机颜色
        text_color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )

        # 随机位置和旋转
        x = 20 + i * 25 + random.randint(-5, 5)
        y = 15 + random.randint(-5, 5)
        angle = random.randint(-15, 15)

        # 创建字符图像并旋转
        char_image = Image.new('RGBA', (30, 30), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((0, 0), char, fill=text_color, font=font)
        char_image = char_image.rotate(angle, expand=1)

        # 将旋转后的字符粘贴到主图像
        image.paste(char_image, (int(x), int(y)), char_image)

    # 添加干扰线
    for _ in range(5):
        line_color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=line_color, width=1)

    # 添加噪点
    for _ in range(100):
        noise_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=noise_color)

    return image, captcha_text

def captcha_mian():
    # 生成验证码
    captcha_image, captcha_text = generate_captcha()

    # 保存验证码图片
    # output_dir = "captchas"
    # os.makedirs(output_dir, exist_ok=True)
    captcha_image.save(f"static/tmp_captcha.png")


if __name__ == "__main__":
    # 生成验证码
    # captcha_image, captcha_text = generate_captcha()
    #
    # # 保存验证码图片
    # #output_dir = "captchas"
    # #os.makedirs(output_dir, exist_ok=True)
    # captcha_image.save(f"static/tmp_captcha.png")
    #
    # # 显示验证码图片（如果环境支持）
    # print(captcha_text)
    # captcha_image.show()
    image, answer = generate_math_captcha()
    image.save("math_captcha.png")
    print("验证码答案:", answer)