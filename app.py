#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil
import dateutil.parser
import babel
import os
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
db.init_app(app)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  custom_areas = []
  for v in Venue.query.all():
    contains_loc = False
    area_id = 0
    for area in custom_areas:
        if area["city"] == v.city and area["state"] == v.state:
            contains_loc = True
        else:
            area_id += 1
    if contains_loc:
        custom_areas[area_id]["venues"].append({
            "id": v.id,
            "name": v.name,
            "num_upcoming_shows": 0
        })
    else:
        custom_areas.append({
            "city": v.city,
            "state": v.state,
            "venues": [{
                "id": v.id,
                "name": v.name,
                "num_upcoming_shows": 0
            }]
        })
  return render_template('pages/venues.html', areas=custom_areas)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  search_query = Venue.query.all()
  search_result=[]
  for venue in search_query:
    if search_term.lower() in venue.name.lower():
        search_result.append(venue)
  response = { "count": len(search_result), "data": [] }
  for venue in search_result:
    response["data"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": 0
    })
  return render_template('pages/search_venues.html', results=response, search_query=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    past_shows = []
    past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()   
    for show in past_shows_query:
        past_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist_name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": show.start_time
        })
    
    upcoming_shows = []
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time>=datetime.now()).all()   
    for show in upcoming_shows_query:
        upcoming_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist_name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": show.start_time
        })

    venue = Venue.query.filter_by(id=venue_id).first()
    data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "seeking_talent": venue.seeking_talent,
            "image_link": venue.image_link,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm(request.form, meta={'csrf': False})

    try:
        if form.validate_on_submit():
            with app.app_context():
                temp_seeking_talent = False
                if "seeking_talent" in request.form:
                    temp_seeking_talent = True
                new_venue = Venue(
                    name = form.name.data,
                    city = form.city.data,
                    state = form.state.data,
                    address = form.address.data,
                    phone = form.phone.data,
                    genres = form.genres.data,
                    facebook_link = form.facebook_link.data,
                    image_link = form.image_link.data,
                    website = form.website_link.data,
                    seeking_talent = form.seeking_talent.data,
                    seeking_description = form.seeking_description.data
                )
                db.session.add(new_venue)
                db.session.commit()

                # on successful db insert, flash success
                flash('Venue ' + request.form['name'] + ' was successfully listed!')
        else:
            for error in form.errors:
                flash(f"Error with field {error}. ", 'error')
            return redirect(url_for('create_venue_form'))
    except:
        db.session.rollback()
        flash('We encountered an error when trying to list venue ' + request.form['name'] + '.', 'error')
    finally:
        db.session.close()
        return redirect(url_for('index'))

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    with app.app_context():
        db.session.delete(Venue.query.filter_by(id=venue_id).first())
        db.session.commit()
    flash('The venue has been successfully deleted.')
  except:
    db.session.rollback()
    flash('We encountered an error when trying to delete the venue.')
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  # Saves the search term in a variable
  search_term = request.form.get('search_term', '')
  search_result=[]

  # Loops through all artists and compares them to the lowercase prompt
  for artist in Artist.query.all():
    if search_term.lower() in artist.name.lower():
        search_result.append(artist)

  # data to be returned
  response = { "count": len(search_result), "data": [] }

  # takes all of the saved artists and adds them to the response data
  for artist in search_result:
    response["data"].append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": 0
    })
  return render_template('pages/search_artists.html', results=response, search_query=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Gets the correct artist using artist_id
    past_shows = []
    past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()   
    for show in past_shows_query:
        past_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue_name,
            "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
            "start_time": show.start_time
        })
    
    upcoming_shows = []
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>=datetime.now()).all()   
    for show in upcoming_shows_query:
        upcoming_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue_name,
            "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
            "start_time": show.start_time
        })

    artist = Artist.query.filter_by(id=artist_id).first()
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "image_link": artist.image_link,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=Artist.query.filter_by(id=artist_id).first())

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form, meta={'csrf': False})

    if form.validate_on_submit():
        artist = Artist.query.filter_by(id=artist_id).first()
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.commit()
        # TODO: insert form data as a new Venue record in the db, instead
        return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        for error in form.errors:
            flash(f"Error with field {error}. ", 'error')
        return redirect(url_for('edit_artist_submission', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=Venue.query.filter_by(id=venue_id).first())

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate_on_submit():
        venue = Venue.query.filter_by(id=venue_id).first()
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        db.session.commit()

        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        for error in form.errors:
            flash(f"Error with field {error}. ", 'error')
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    form = ArtistForm(request.form, meta={'csrf': False})
    try:
        if form.validate_on_submit():
            with app.app_context():
                db.session.add(
                    Artist(
                        name = form.name.data,
                        city = form.city.data,
                        state = form.state.data,
                        phone = form.phone.data,
                        genres = form.genres.data,
                        facebook_link = form.facebook_link.data,
                        image_link = form.image_link.data,
                        website = form.website_link.data,
                        seeking_venue = form.seeking_venue.data,
                        seeking_description = form.seeking_description.data
                    ))
                db.session.commit()

            # on successful db insert, flash success
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        else:
            for error in form.errors:
                flash(f"Error with field {error}. ", 'error')
            return redirect(url_for('create_artist_submission'))
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('We encountered an error when trying to list artist ' + request.form['name'] + '.', 'error')
    finally:
        db.session.close()
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  show_list = Show.query.all()
  data = []
  for show in show_list:
    data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue_name,
        "artist_id": show.artist_id,
        "artist_name": show.artist_name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": show.start_time
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        with app.app_context():
            db.session.add(Show(
                artist_id = request.form['artist_id'],
                artist_name = Artist.query.filter_by(id=request.form['artist_id']).first().name,
                venue_id = request.form['venue_id'],
                venue_name = Venue.query.filter_by(id=request.form['venue_id']).first().name,
                start_time = request.form['start_time']
            ))
            db.session.commit()

        # on successful db insert, flash success
        flash('The show was successfully listed!')
    except:
        db.session.rollback()
        flash('We encountered an error when trying to list the show.')
    finally:
        db.session.close()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
'''
if __name__ == '__main__':
    app.run()
'''

# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7000))
    app.run(host='0.0.0.0', port=port)
