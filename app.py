from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Animal, Status, Media, Disease, Vaccine, Color, AnimalType, FurType
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)

# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animals.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных и миграций
db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    animals = Animal.query.all()
    return render_template('index.html', animals=animals)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        animal = Animal(
            photo=request.form['photo'],
            animal_type_id=request.form['animal_type_id'],
            name=request.form['name'],
            birth_year=request.form['birth_year'],
            gender=request.form['gender'],
            color_id=request.form['color_id'],
            fur_type_id=request.form['fur_type_id'],
            phenotype=request.form['phenotype'],
            description=request.form['description'],
            history=request.form['history'],
            article_text=request.form['article_text'],
            important=request.form.get('important') == 'on',
            sterilization=request.form.get('sterilization') == 'on',
            chip=request.form.get('chip') == 'on'
        )
        db.session.add(animal)
        db.session.commit()
        return redirect(url_for('index'))

    # Получаем данные для выпадающих списков
    animal_types = AnimalType.query.all()
    colors = Color.query.all()
    fur_types = FurType.query.all()

    return render_template('create.html', animal_types=animal_types, colors=colors, fur_types=fur_types)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    animal = Animal.query.get_or_404(id)

    if request.method == 'POST':
        animal.photo = request.form['photo']
        animal.animal_type_id = request.form['animal_type_id']
        animal.name = request.form['name']
        animal.birth_year = request.form['birth_year']
        animal.gender = request.form['gender']
        animal.color_id = request.form['color_id']
        animal.fur_type_id = request.form['fur_type_id']
        animal.phenotype = request.form['phenotype']
        animal.description = request.form['description']
        animal.history = request.form['history']
        animal.article_text = request.form['article_text']

        # Обновляем булевы значения
        animal.important = request.form.get('important') == 'on'
        animal.sterilization = request.form.get('sterilization') == 'on'
        animal.chip = request.form.get('chip') == 'on'

        db.session.commit()

        return redirect(url_for('index'))

    animal_types = AnimalType.query.all()
    colors = Color.query.all()
    fur_types = FurType.query.all()

    return render_template('edit.html', animal=animal,
                           animal_types=animal_types, colors=colors, fur_types=fur_types)


@app.route('/delete/<int:id>')
def delete(id):
    animal = Animal.query.get_or_404(id)
    db.session.delete(animal)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET'])
def admin():
   animals = Animal.query.all()
   animal_count = len(animals)

   return render_template('admin.html', animals=animals, animal_count=animal_count)

@app.route('/import', methods=['POST'])
def import_animals():
   if 'file' not in request.files:
       return redirect(request.url)

   file = request.files['file']
   
   if file.filename == '':
       return redirect(request.url)

   if file:
       df = pd.read_excel(file)  # Чтение Excel файла
       for index, row in df.iterrows():
           animal_data_dict= {
               "name": row['Имя'],
               "photo": row['Фото'],
               "birth_year": row['Год рождения'],
               "gender": row['Пол'],
               "color_id": row['Цвет ID'],  
               "animal_type_id": row['Тип ID'], 
               "fur_type_id": row['Тип шерсти ID'],  
               "phenotype": row['Фенотип'],
               "description": row['Описание'],
               "history": row['История'],
               "article_text": row['Текст статьи'],
               "important": row.get('Важное', False),
               "sterilization": row.get('Стерилизация', False),
               "chip": row.get('Чип', False),
           }
           animal= Animal(**animal_data_dict) 
           db.session.add(animal)
       db.session.commit()
       
       return redirect(url_for('admin'))

@app.route('/statistics')
def statistics():
   labels=[]
   sizes=[]
   
   for type_name,count in (db.session.query(
         AnimalType.name,
         func.count(Animal.id)).join(Animal).group_by(
         AnimalType.name).all()):
       labels.append(type_name)
       sizes.append(count)

   plt.figure(figsize=(10 ,6))
   plt.bar(labels,sizes )
   plt.title("Количество животных по типам")
   plt.xlabel("Тип животного")
   plt.ylabel("Количество")

   return send_file(img ,mimetype='image.png')

@app.route('/register', methods=['GET', 'POST'])
def register():
     form= RegisterForm()
     if form.validate_on_submit():
         new_user= User(username=form.username.data,password=form.password.data) 
         new_user.password= generate_password_hash(form.password.data) 
         db.session.add(new_user) 
         db.session.commit() 
         return redirect(url_for('login')) 

     return render_template('register.html' ,form=form )

@app.route('/login', methods=['GET', 'POST'])
def login():
     form= LoginForm()
     if form.validate_on_submit():
         user= User.query.filter_by(username=form.username.data).first() 
         if user and check_password_hash(user.password ,form.password.data): 
             login_user(user) 
             return redirect(url_for('admin')) 

     return render_template('login.html' ,form=form )

@app.route('/logout') 
def logout(): 
     return redirect(url_for('login'))



if __name__ == '__main__':
    with app.app_context():  # Создаем контекст приложения
        db.create_all()
    app.run(debug=True)
