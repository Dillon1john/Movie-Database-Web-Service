from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL
import requests
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
# Optional: But it will silence the depreciation waeining in the console
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)
db.sessionmaker(autoflush=True)

# movie_url = "https://api.themoviedb.org/api_key=3167fb51fa3352e2a854ebd062755d44"

movie_url = f"https://api.themoviedb.org/3/search/movie?api_key=3167fb51fa3352e2a854ebd062755d44&language=en-US&query="
IMAGE_URL = "https://image.tmdb.org/t/p/w500/"
response = requests.get(movie_url + 'Inception')
# print(json.dumps(response.json()['results'], indent=1))
movie_list = []
movie = "Inception"
response = requests.get(movie_url + movie)

similar_movies = response.json()['results']
for movies in similar_movies:
    movie_list.append("".join(movies['title']) + "-" + "".join(movies['release_date']))
    # print("".join(movies['title']))
print(movie_list)


# CREATE TABLE
with app.app_context():
    class Movie(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        year = db.Column(db.String(250), unique=True, nullable=False)
        description = db.Column(db.String(1250), unique=True, nullable=False)
        rating = db.Column(db.String(250), nullable=False)
        ranking = db.Column(db.String(250), nullable=True)
        review = db.Column(db.String(750), nullable=False)
        img_url = db.Column(db.String(500), nullable=False)

        # Optional: will allow each book object to be identified by its title when printed
        def _repr__(self):
            return f'<Movie {self.title}'


    db.create_all()


    class MovieForm(FlaskForm):
        # stars = ['⭐️', '⭐⭐', '⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐⭐⭐']
        title = StringField("Movie Name:", validators=[DataRequired()])
        # year = StringField("Year:", validators=[DataRequired()])
        # description = StringField("Description:", validators=[DataRequired()])
        # rating = StringField("Rating:", validators=[DataRequired()])
        # ranking = StringField("Ranking:", validators=[DataRequired()])
        # review = StringField("Review:", validators=[DataRequired()])
        # img_url = StringField("image URL:", validators=[DataRequired(), URL()])
        submit = SubmitField("Add Movie")
        # rating = SelectField("Rating:", validators=[DataRequired()], choices=stars)


    class EditForm(FlaskForm):
        rating = StringField("Your Rating Out of 10 e.g.7.5:", validators=[DataRequired()])
        review = StringField("Your Review:", validators=[DataRequired()])
        submit = SubmitField("Done")
        # rating = SelectField("Rating:", validators=[DataRequired()], choices=stars)


    all_movies = db.session.query(Movie).all()


    @app.route("/")
    def home():
        sorted_movies = db.session.query(Movie).order_by(Movie.rating).all()
        movie_total = db.session.query(Movie).count()
        for movie in sorted_movies:
            movie.ranking = movie_total
            db.session.commit()
            movie_total -= 1

        return render_template("index.html", movies=sorted_movies)


    @app.route("/add", methods=['POST', 'GET'])
    def add():
        form = MovieForm()
        if form.validate_on_submit():
            movie_list = makeList(form)
            return render_template('select.html', movie_list=movie_list, movie_name=form.title.data)
        return render_template('add.html', form=form)


    def makeList(form):
        movie_dict = {}
        movie = form.title.data
        response = requests.get(movie_url + movie)
        similar_movies = response.json()['results']
        for movies in similar_movies:
            movie_dict[movies['id']] = [movies['title'], movies['release_date']]
        print(movie_dict)
        return movie_dict


    @app.route("/select")
    def select():
        movie_list = []
        movie_name = ""
        return render_template('select.html', movie_list=movie_list, movie_name=movie_name)


    @app.route("/edit?<int:id>?<string:name>", methods=['POST', 'GET'])
    def edit(id, name):
        form = EditForm()
        if form.validate_on_submit():
            exists = db.session.query(Movie).filter_by(id=id).first() is not None
            if exists:
                db.session.query(Movie).filter_by(id=id).update({'rating': form.rating.data})
                db.session.commit()
                db.session.query(Movie).filter_by(id=id).update({'review': form.review.data})
                db.session.commit()
                return redirect(url_for('home'))
            else:
                response = requests.get(movie_url + name)
                movies = response.json()['results']
                for movie in movies:
                    if movie['id'] == id:
                        new_movie = Movie(id=id,
                                          title=movie['title'],
                                          year=movie['release_date'],
                                          description=movie['overview'],
                                          rating=form.rating.data,
                                          ranking=None,
                                          review=form.review.data,
                                          img_url=f"{IMAGE_URL}{movie['poster_path']}")
                        db.session.add(new_movie)
                        db.session.commit()
                return redirect(url_for('home'))
        return render_template('edit.html', form=form)


    @app.route('/delete?<int:id>')
    def delete(id):
        movie_to_delete = db.session.query(Movie).filter_by(id=id).first()
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for('home'))
if __name__ == '__main__':
    app.run(debug=True)
