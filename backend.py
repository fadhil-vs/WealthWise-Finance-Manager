from os import error
import sqlite3

def view_transaction_function(uid):
    transactions=[]
    conn = sqlite3.connect('mydb.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions_{0}".format(uid))
    transaction = cur.fetchall()
    conn.close()
    for i in transaction:
      d={'id':i[0],'date':i[1],'amount':i[2],'type':i[3],'category':i[4],'description':i[5]}
      transactions.append(d)
    return transactions


def save_transaction(uid, date, amount, ttype, category, description):
    conn = sqlite3.connect('mydb.db')
    cur = conn.cursor()

    try:
        table_name = f"transactions_{uid}"
        print(table_name)
        cur.execute(f'SELECT id FROM "{table_name}" ORDER BY id DESC LIMIT 1')
        row = cur.fetchone()
        if row is None:
            new_id = 1
        else:
            new_id = int(row[0])+1

        cur.execute(f'''
            INSERT INTO "{table_name}" (id, date, amount, type, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_id, date, amount, ttype, category, description))

        conn.commit()
    except error:
        pass
        print(error)
        
    finally:
        conn.close()
