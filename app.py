from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# تعريف نموذج الاشتراك
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_key = db.Column(db.String(50), unique=True, nullable=False)
    app_name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=True)
    expiry_date = db.Column(db.DateTime, nullable=False)

# إنشاء الجداول
with app.app_context():
    db.create_all()

def check_subscription_status(app_key):
    """التحقق من حالة الاشتراك."""
    subscription = Subscription.query.filter_by(app_key=app_key).first()
    if not subscription:
        return {"active": False, "message": "مفتاح التطبيق غير صالح."}

    current_date = datetime.datetime.now()
    if current_date > subscription.expiry_date:
        subscription.active = False
        db.session.commit()
        return {"active": False, "message": "انتهت صلاحية الاشتراك."}

    return {"active": subscription.active, "message": "الاشتراك فعال."}

@app.route('/')
def index():
    """عرض الصفحة الرئيسية."""
    return render_template('index.html')

@app.route('/add_subscription', methods=['GET', 'POST'])
def add_subscription():
    """إضافة اشتراك جديد."""
    if request.method == 'POST':
        app_key = request.form.get("app_key")
        expiry_date = request.form.get("expiry_date")

        if not app_key or not expiry_date:
            return render_template('add_subscription.html', error="يرجى توفير جميع البيانات.")

        try:
            expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            return render_template('add_subscription.html', error="تنسيق تاريخ الانتهاء غير صحيح. استخدم 'YYYY-MM-DD'.")

        new_subscription = Subscription(
            app_key=app_key,
            app_name="New App",
            active=True,
            expiry_date=expiry_date
        )
        db.session.add(new_subscription)
        db.session.commit()

        return redirect(url_for('list_subscriptions'))

    return render_template('add_subscription.html')

@app.route('/list_subscriptions')
def list_subscriptions():
    """عرض جميع الاشتراكات."""
    subscriptions = Subscription.query.all()
    return render_template('list_subscriptions.html', subscriptions=subscriptions)

@app.route('/check_subscription_ui', methods=['GET', 'POST'])
def check_subscription_ui():
    """التحقق من الاشتراك باستخدام واجهة المستخدم."""
    result = None
    if request.method == 'POST':
        app_key = request.form.get("app_key")
        if app_key:
            result = check_subscription_status(app_key)
        else:
            result = {"active": False, "message": "يرجى توفير مفتاح التطبيق."}

    return render_template('check_subscription.html', result=result)

@app.route('/error')
def error():
    return render_template('error.html', message="حدث خطأ ما.")


@app.route('/check_subscription', methods=['GET'])
def check_subscription():
    """التحقق من الاشتراك عبر واجهة برمجة التطبيقات."""
    app_key = request.args.get("app_key")
    if not app_key:
        return jsonify({"active": False, "message": "يرجى توفير مفتاح التطبيق."}), 400

    status = check_subscription_status(app_key)
    return jsonify(status)

@app.route('/edit_subscription/<int:id>', methods=['GET', 'POST'])
def edit_subscription(id):
    """تعديل أو تمديد الاشتراك."""
    subscription = Subscription.query.get_or_404(id)

    if request.method == 'POST':
        expiry_date = request.form.get("expiry_date")
        if not expiry_date:
            return render_template('edit_subscription.html', subscription=subscription, error="يرجى توفير تاريخ الانتهاء.")
        
        try:
            expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            return render_template('edit_subscription.html', subscription=subscription, error="تنسيق تاريخ الانتهاء غير صحيح. استخدم 'YYYY-MM-DD'.")
        
        subscription.expiry_date = expiry_date
        subscription.active = True if expiry_date > datetime.datetime.now() else False
        db.session.commit()
        return redirect(url_for('list_subscriptions'))

    return render_template('edit_subscription.html', subscription=subscription)

@app.route('/deactivate_subscription/<int:id>', methods=['POST'])
def deactivate_subscription(id):
    """إلغاء الاشتراك."""
    subscription = Subscription.query.get_or_404(id)
    subscription.active = False
    db.session.commit()
    return redirect(url_for('list_subscriptions'))       

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)