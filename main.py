from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SEARCH_MOVIE_URL = "https://api.themoviedb.org/3/search/movie"
DETAILS_MOVIE_URL = "https://api.themoviedb.org/3/movie/"
MOVIE_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

headers = {
    "accept": "application/json",
    "Authorization": os.getenv("TOKEN")
}

class editForm(FlaskForm):
    rating = DecimalField(label="Your Rating Out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")
    
class addForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_NAME")
Bootstrap5(app)
db = SQLAlchemy()
db.init_app(app)

class Movie(db.Model):
    id  = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True ,nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True, default="0")
    ranking = db.Column(db.Integer, nullable=True, default="0")
    review = db.Column(db.String(250), nullable=True, default="None")
    img_url = db.Column(db.String(250), nullable=False)
    
with app.app_context(): 
    db.create_all()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all() # convert ScalarResult to Python List
    movies_len = len(all_movies)
    print(all_movies)
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()    
    return render_template("index.html", movies = all_movies, movies_len = movies_len)

@app.route("/edit",methods=["GET","POST"])
def edit():
    edit_form = editForm()
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    if edit_form.validate_on_submit():
        movie_selected.rating = float(edit_form.rating.data)
        movie_selected.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie = movie_selected, form = edit_form)

@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add",methods=["GET","POST"])
def add():
    movies_db_name = []
    movies_db = db.session.execute(db.select(Movie)).scalars().all()
    for movie in movies_db:
        movies_db_name.append(movie.title)
    add_form = addForm()
    if add_form.validate_on_submit():
        title = add_form.title.data
        param = {
            "query":title
        }
        response = requests.get(SEARCH_MOVIE_URL, headers=headers, params=param)
        response.raise_for_status()
        movie_data = response.json()
        movies = movie_data["results"]
        if movies == []:
            is_empty = True
        else:
            is_empty = False
        return render_template("select.html", movies = movies, is_empty=is_empty, movies_db_name = movies_db_name)
    return render_template("add.html", form = add_form)

@app.route("/find")
def find():
    movie_id = request.args.get("id")
    response = requests.get(url=f"{DETAILS_MOVIE_URL}{movie_id}", headers = headers)
    response.raise_for_status()
    movie_data = response.json()
    new_movie = Movie(
        title=movie_data["title"],
        year=movie_data["release_date"].split("-")[0],
        description=movie_data["overview"],
        img_url=f"{MOVIE_IMAGE_URL}/{movie_data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit',id=new_movie.id))

if __name__ == '__main__':
    app.run()
