from flask import Flask,redirect,url_for,request,render_template,flash,session
import mysql.connector
from key import secret_key,salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail

app = Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'
mydb = mysql.connector.connect(host='localhost', user='root', password='admin', db='calorieCounter')

@app.route('/')
def index():
    return render_template('title.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('Username is already in use')
            return render_template('registration.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        data={'username':username,'password':password,'email':email}
        subject='Email Confirmation'
        body=f"Welcome to our Calorie Counter Application {username}!!!\n\nThanks for registering on our application....\nClick on this link to confirm your registration - {url_for('confirm',token=token(data),_external=True)}\n\n\n\nWith Regards,\nCalorie Counter Team"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('registration'))
    return render_template('registration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception:
        flash('Link expired register again')
        return redirect(url_for('registration'))
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users values(%s,%s,%s)',[data['username'],data['email'],data['password']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))
        
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('You are successfully logged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/about')
def about():
    if session.get('user'):
        return render_template('about.html')
    else:
        return redirect(url_for('login'))
    

@app.route('/home')
def home():
    if session.get('user'):
        return render_template('home.html')
    else:
        return redirect(url_for('login'))

@app.route('/calorie', methods=["GET","POST"])
def calorie():
    if session.get('user'):
        if request.method == 'POST':
            try:
                weight = int(request.form['weight'])
                height = int(request.form['height'])
                age = int(request.form['age'])
                gender = request.form['gender']
                if gender == 'male':    
                    bmr = (10*weight)+(6.25*height)-(5*age)+5
                else:
                    bmr = (10*weight)+(6.25*height)-(5*age)-161
                item = []
                quantity = []
                item.append(request.form['item1'])
                item.append(request.form['item2'])
                item.append(request.form['item3'])
                item.append(request.form['item4'])
                item.append(request.form['item5'])
                item.append(request.form['item6'])
                item.append(request.form['item7'])
                item.append(request.form['item8'])
                quantity.append(float(request.form['quantity1']))
                quantity.append(float(request.form['quantity2']))
                quantity.append(float(request.form['quantity3']))
                quantity.append(float(request.form['quantity4']))
                quantity.append(float(request.form['quantity5']))
                quantity.append(float(request.form['quantity6']))
                quantity.append(float(request.form['quantity7']))
                quantity.append(float(request.form['quantity8']))
                cursor=mydb.cursor(buffered=True)
                username=session.get('user')
                cal = 0.0
                try:
                    for i in range(0,8):
                        cursor.execute('select cal from calories where food_item = %s',[item[i]])  
                        cal += (quantity[i]*(cursor.fetchone()[0]))
                except:
                    flash('Enter the enter details correctly.')
                    return redirect(url_for('calorie'))
                diff = cal-bmr
                cursor.execute('insert into userCalCount(weight, height, age, gender, bmr, final_result, food_cal, username) values(%s,%s,%s,%s,%s,%s,%s,%s)',[weight, height, age, gender, bmr, diff, cal, username])
                mydb.commit()
                diff = abs(diff)
                data = [weight, height, age, gender, bmr, diff, cal, username]
                print(data)
                if bmr > cal:
                    flash(f'You need to take {diff} more calories')
                    return render_template('result.html',data=data)
                else:
                    flash(f'You are taking {diff} more calories than required')
                    return render_template('result.html',data=data)
            except:
                return redirect('calorie.html')
        return render_template('calorie.html')
    else:
        return redirect(url_for('login'))

@app.route('/result')
def result():
    if session.get('user'):
        return render_template('result.html')
    else:
        return redirect(url_for('login'))

@app.route('/history')
def history():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from usercalcount where username = %s order by cal_date desc',[username])
        data=cursor.fetchall()
        cursor.close()
        return render_template('history.html',data=data)
    else:
        return redirect(url_for('login'))
    
@app.route('/delete/<nid>')
def delete(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from userCalCount where cid=%s',[nid])
        mydb.commit()
        cursor.close()
        flash('Notes Deleted.')
        return redirect(url_for('history'))
    else:
        return redirect(url_for('login'))
    
@app.route('/view/<nid>')
def view(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select weight, height, age, gender, bmr, final_result, food_cal, username from userCalCount where cid=%s',[nid])
        data = cursor.fetchone()
        cursor.close()
        diff = data[5]
        if diff < 0:
            flash(f'You need to take {diff} more calories')
            return render_template('result.html',data=data)
        else:
            flash(f'You are taking {diff} more calories than required')
            return render_template('result.html',data=data)
    else:
        return redirect(url_for('login'))
    
@app.route('/forgotpassword', methods=["GET","POST"])
def forgotpassword():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        confirmPassword = request.form['password1']
        if password != confirmPassword:
            flash('Both passwords are not same')
            return redirect(url_for('forgotpassword'))
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email from users where username=%s',[username])
        email = cursor.fetchone()[0]
        cursor.close()
        data={'username':username,'password':password, 'email':email}
        subject='Forgot Password Confirmation'
        body=f"Welcome to our Calorie Counter Application {username}!!!\n\nThis is your account's password reset confirmation email....\nClick on this link to confirm your reset password - {url_for('reset',token=token(data),_external=True)}\n\n\n\nWith Regards,\nCalorie Counter Team"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('forgotpassword'))
    return render_template('forgotpassword.html')

@app.route('/reset/<token>')
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception:
        flash('Link expired reset your password again')
        return redirect(url_for('forgotpassword'))
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        password = data['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('update users set password = %s where username = %s',[password, username])
        mydb.commit()
        cursor.close()
        flash('Password Reset Successful!')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(use_reloader = True, debug= True)


