from types import MethodType
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from backend import view_transaction_function , save_transaction
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route('/logout', methods=['POST', 'GET'])
def logout():
  session['current_user_id'] = ""
  return redirect(url_for('login'))


#LANDING PAGE----------------------------------------------------------------------------
@app.route('/')
def home():
  session['current_page'] = 'landing'
  session['previous_page'] = ''
  session['navigation'] = True
  return render_template('landing.html')


#DASHBOARD---------------------------------------------------------------------------------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
  if request.method == 'GET':
    if "current_user_id" in session and session['current_user_id'] != "":
      session['previous_page'] = session['current_page']
      session['current_page'] = 'dashboard'
      cur=sqlite3.connect('mydb.db').cursor()
    
      cur.execute(
          f"SELECT SUM(amount) FROM transactions_{session['current_user_id']} WHERE type = 'income'")
      income = cur.fetchone()[0]
      if income==None:
        income=0
      cur.execute(f"SELECT SUM(amount) FROM transactions_{session['current_user_id']} WHERE type = 'expense'")
      expense = cur.fetchone()[0]
      if expense==None:
        expense=0
          
      net=income-expense
      return render_template('dashboard.html',net=net,income=income,expense=expense)
    else:
      return redirect(url_for("login"))


#ADD TRANSACTION----------------------------------------------------------------------------
@app.route('/add_transaction', methods=["GET", "POST"])
def add_transaction():
  if request.method == 'GET':
    if session['current_user_id'] != "":
      session['previous_page'] = session['current_page']
      session['current_page'] = 'add_transaction'
      return render_template('add_transaction.html', form_data={})
    else:
      return redirect(url_for("login"))
  elif request.method == 'POST':
    date = request.form.get('date')
    amount = request.form.get('amount')
    type = request.form.get('type')
    category = request.form.get('category')
    description = request.form.get('description')

    save_transaction(session['current_user_id'], date,
                                              amount, type, category,
                                              description)
    return redirect(url_for('add_transaction'))


#LOGIN--------------------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'GET':
    session['previous_page'] = session['current_page']
    session['current_page'] = 'login'
    return render_template('login.html')
  elif request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')

    with sqlite3.connect('mydb.db') as con:
      cur = con.cursor()
      cur.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                  (username, password))
      user = cur.fetchone()

  if not all([username, password]):
    return render_template('login.html',
                           login_error_message="Please fill all the fields")
  elif not user:
    return render_template('login.html',
                           login_error_message="Invalid username or password")
  else:
    session['current_user_id'] = user[0]
    session['current_user_name'] = user[1]
    return redirect(url_for('dashboard'))


#SIGNUP--------------------------------------------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
  if request.method == 'GET':
    session['previous_page'] = session['current_page']
    session['current_page'] = 'signup'
    return render_template('signup.html')

  elif request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('conf_password')
    email = request.form.get('email')
    security_question = request.form.get('security_question')
    security_answer = request.form.get('security_answer')

    con = sqlite3.connect('mydb.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username, ))

    if password != confirm_password:
      return render_template('signup.html',
                             signup_error_message="Passwords do not match")
    elif not all([
        username, password, confirm_password, email, security_question,
        security_answer
    ]):
      return render_template('signup.html',
                             signup_error_message="Please fill all the fields")
    elif cur.fetchone():
      return render_template('signup.html',
                             signup_error_message="Username already exists")
    else:
      cur.execute(
          'INSERT INTO users (username, password, email, security_qn, answer) VALUES (?, ?, ?, ?, ?)',
          (username, password, email, security_question, security_answer))
      cur.execute(f'SELECT * FROM users WHERE username = "{username}"')
      user_id = cur.fetchone()[0]
      cur.execute(f"DROP TABLE IF EXISTS transactions_{user_id}")
      cur.execute(
          f"CREATE TABLE transactions_{user_id} (id TEXT PRIMARY KEY,date TEXT,amount REAL,type TEXT, category TEXT,description TEXT)"
      )
      con.commit()
      cur.close()
      con.close()
      return redirect(url_for('login'))


#FORGOT PASSWORD----------------------------------------------------------------------------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_pass():
  if request.method == 'GET':
    session['previous_page'] = session['current_page']
    session['current_page'] = 'forgot_pass'
    return render_template('forgot_pass.html')
  elif request.method == 'POST':
    username = request.form.get('username')
    security_question = request.form.get('security_question')
    security_answer = request.form.get('security_answer')

    with sqlite3.connect('mydb.db') as con:
      cur = con.cursor()
      cur.execute('SELECT * FROM users WHERE username = ?', (username, ))
      details = cur.fetchone()

    if not all([username, security_question, security_answer]):
      return render_template('forgot_pass.html',
                             forgot_error_message="Please fill all the fields")
    elif not details:
      return render_template('forgot_pass.html',
                             forgot_error_message="Username does not exist")
    elif details[4] != security_question or details[5] != security_answer:
      return render_template(
          'forgot_pass.html',
          forgot_error_message="Security question or answer is incorrect")
    else:
      session['current_user_id'] = details[0]
      return redirect(url_for('reset_pass'))


#RESET PASSWORD----------------------------------------------------------------------------
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_pass():
  user_id = session.get('user_id')
  if request.method == 'GET':
    session['previous_page'] = session['current_page']
    session['current_page'] = 'reset_pass'
    return render_template('reset_pass.html')

  elif request.method == 'POST':
    password = request.form.get('password')
    confirm_password = request.form.get('conf_password')

    con = sqlite3.connect('mydb.db')
    cur = con.cursor()

    if not all([password, confirm_password]):
      return render_template('reset_pass.html',
                             reset_error_message="Please fill all the fields")
    elif password != confirm_password:
      return render_template('reset_pass.html',
                             reset_error_message="Passwords do not match")
    else:
      cur.execute('UPDATE users SET password = ? WHERE id = ?',
                  (password, user_id))
      con.commit()
      cur.close()
      con.close()
      session.pop('user_id', None)
      return redirect(url_for('login'))


#VIEW TRANSACTION----------------------------------------------------------------------------
@app.route('/view_transaction', methods=['GET', 'POST'])
def view_transaction():
  if request.method == 'GET':
    session['previous_page'] = session['current_page']
    session['current_page'] = 'view_transaction'
    transactions =view_transaction_function(
        session['current_user_id'])
    return render_template('view_transaction.html', transactions=transactions)
  elif request.method == 'POST':
    pass


#EDIT TRANSACTION----------------------------------------------------------------------------
@app.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    conn = sqlite3.connect('mydb.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM transactions_{session['current_user_id']} WHERE id = ?''', (transaction_id,))        
    transaction=cur.fetchone()
    if transaction is None:
        conn.close()
        return "Transaction not found", 404

    if request.method == 'POST':
        date = request.form['date']
        amount = request.form['amount']
        type_ = request.form['type']
        category = request.form['category']
        description = request.form.get('description', '')

        conn.execute(f'''
            UPDATE transactions_{session['current_user_id']}
            SET date = ?, amount = ?, type = ?, category = ?, description = ?
            WHERE id = ?
        ''', (date, amount, type_, category, description, transaction_id))
        conn.commit()
        conn.close()

        return redirect(url_for('view_transaction'))

    conn.close()
    form_data = {
        'date': transaction[1],
        'amount': transaction[2],
        'type': transaction[3],
        'category': transaction[4],
        'description': transaction[5] or ''
    }
    return render_template('edit_transaction.html', transaction_id=transaction_id, form_data=form_data)

#DELETE TRANSACTION----------------------------------------------------------------------------
@app.route('/delete_transaction/<int:transaction_id>', methods=['POST', 'GET'])
def delete_transaction(transaction_id):
  conn = sqlite3.connect('mydb.db')
  cur = conn.cursor()
  cur.execute(
      f"""DELETE FROM transactions_{session['current_user_id']} WHERE id = {transaction_id}""")
  conn.commit()
  cur.close()
  return redirect(url_for('view_transaction'))

#about us-------------------------------------------------------------------------------------- 
@app.route('/about_us')
def about_us():
  session['previous_page'] = session['current_page']
  session['current_page'] = 'about_us'
  return render_template('about_us.html',user_id=session['current_user_id'],user_name=session['current_user_name'])

#analysis--------------------------------------------------------------------------------------
@app.route('/analysis')
def analysis():
    session['previous_page'] = session['current_page']
    session['current_page'] = 'analysis'

    label_income, values_income = [], []
    label_exp, values_exp = [], []

    conn = sqlite3.connect('mydb.db')
    cur = conn.cursor()

    # Income
    cur.execute(f"""
        SELECT category, SUM(amount)
        FROM transactions_{session['current_user_id']}
        WHERE type = 'income'
        GROUP BY category
    """)
    for row in cur.fetchall():
        label_income.append(row[0])
        values_income.append(row[1])

    # Expense
    cur.execute(f"""
        SELECT category, SUM(amount)
        FROM transactions_{session['current_user_id']}
        WHERE type = 'expense'
        GROUP BY category
    """)
    for row in cur.fetchall():
        label_exp.append(row[0])
        values_exp.append(row[1])

    cur.close()
    conn.close()
    if label_exp == [] and label_income == []:
      return render_template(
          'analyse.html',
          graph1=False,
          graph2=False,
          label1=label_income,
          values1=values_income,
          label2=label_exp,
          values2=values_exp
      )
    elif label_exp == []:
      return render_template(
          'analyse.html',
          graph1=True,
          graph2=False,
          label1=label_income,
          values1=values_income,
          label2=label_exp,
          values2=values_exp
      )

    elif label_income == []:
      return render_template(
          'analyse.html',
          graph1=False,
          graph2=True,
          label1=label_income,
          values1=values_income,
          label2=label_exp,
          values2=values_exp
      )
      
    else:
      return render_template(
          'analyse.html',
          graph1=True,
          graph2=True,
          label1=label_income,
          values1=values_income,
          label2=label_exp,
          values2=values_exp)



#IMPORT EXPORT----------------------------------------------------------------------------
@app.route('/import_export', methods=['GET','POST'])
def import_export():
  if request.method == 'POST':
    session['previous_page'] = session['current_page']
    session['current_page'] = 'import_export'
    return render_template('import_export.html')
  else:
    return render_template('import_export.html')


app.run(host='0.0.0.0', port=8080, debug=True)