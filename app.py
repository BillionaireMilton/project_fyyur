#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from operator import or_
import dateutil.parser
import babel
from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Artist, Venue, Show
from sqlalchemy import or_
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  # instead of just date = dateutil.parser.parse(value)
  if isinstance(value, str):
        date = dateutil.parser.parse(value)
        if format == 'full':
          format="EEEE MMMM, d, y 'at' h:mma"
        elif format == 'medium':
          format="EE MM, dd, y h:mma"
  else:
        date = value
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  areas = list()
  all_venues = Venue.query.all()
  for venue in all_venues:
    area = dict()
    area_position = -1
    if len(areas) == 0:
      area_position = 0
      area = {
        'city': venue.city,
        'state': venue.state,
        'venues': list()
      }
      areas.append(area)
    else:
      for i, area in enumerate(areas):
        if area['city'] == venue.city and area['state'] == venue.state:
          area_position = i
          break
      if area_position < 0:
        area = {
        'city': venue.city,
        'state': venue.state,
        'venues': list()
      }
        areas.append(area)
        area_position = len(areas) - 1
      else:
        area = areas[area_position]
    num_upcoming_shows = Show.query.filter(
                    Show.start_time > datetime.now(),
                    Show.venue_id == venue.id).all()
    dic = { 'id': venue.id, 
            'name': venue.name, 
            'num_upcoming_shows': num_upcoming_shows
          }
    area['venues'].append(dic)
    areas[area_position] = area
  return render_template('pages/venues.html', areas=areas)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  searched = request.form.get('search_term')
  response = Venue.query.filter(
    Venue.name.ilike('%{}%'.format(searched))).all()
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  past_shows = []
  upcoming_shows = []

  data = Venue.query.filter(Venue.id == venue_id).first()

  query_result = None
 

  item = {
    'id': data.id,
    'name': data.name,
    'city': data.city,
    'state': data.state,
    'genres': data.genres.split(','),
    'phone': data.phone,
    'address': data.address,
    'image_link': data.image_link,
    'website_link': data.website_link,
    'facebook_link': data.facebook_link,
    'seeking_talent': data.seeking_talent,
    'seeking_description': data.seeking_description,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': 0,
    'upcoming_shows_count': 0, 
  }

  trigger = Show.query.filter(Show.venue_id == venue_id).all()

  if len(trigger) == 0:
    query_result = item
  else:

    past_shows_query = db.session.query(Show, Artist).join(Artist).filter(Show.venue_id == venue_id).filter(
      Show.start_time < datetime.now()).all()

    for show in past_shows_query:
      past_shows.append(
        {
          "artist_id": show.Show.artist_id,
          "artist_name": show.Artist.name,
          "artist_image_link": show.Artist.image_link,
          "start_time": show.Show.start_time
        }
      )

    upcoming_shows_query = db.session.query(Show, Artist).join(Artist).filter(Show.venue_id == venue_id).filter(
    Show.start_time > datetime.now()).all()

    for show in upcoming_shows_query:
      upcoming_shows.append(
        {
          "artist_id": show.Show.artist_id,
          "artist_name": show.Artist.name,
          "artist_image_link": show.Artist.image_link,
          "start_time": show.Show.start_time
        }
      )
    
    item['past_shows_count'] = len(past_shows)
    item['upcoming_shows_count'] = len(upcoming_shows)
  query_result = item
  return render_template('pages/show_venue.html', venue=query_result)

#  ----------------------------------------------------------------
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
  form = VenueForm(request.form)
  if form.validate():
    try:
      venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        genres = ','.join(form.genres.data),
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )

      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
      flash('Errors: ' + str(message[0]))
      return render_template('forms/new_venue.html', form=form)
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete')
def delete_venue(venue_id):

  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue deleted successfully!')
  except:
    db.session.rollback()
    flash('Error occured! Venue cannot be deleted!')
  finally:
    db.session.close()
  return render_template('pages/home.html')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  searched = request.form.get('search_term')
  response = Artist.query.filter(Artist.name.ilike('%{}%'.format(searched))).all()
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  data = Artist.query.filter(Artist.id == artist_id).first()

  query_result = None
  past_shows = []
  upcoming_shows = []

  item = {
    'id': data.id,
    'name': data.name,
    'city': data.city,
    'state': data.state,
    'genres': data.genres.split(','),
    'phone': data.phone,
    'image_link': data.image_link,
    'website_link': data.website_link,
    'facebook_link': data.facebook_link,
    'seeking_venue': data.seeking_venue,
    'seeking_description': data.seeking_description,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': 0,
    'upcoming_shows_count': 0
  }

  trigger = Show.query.filter(Show.artist_id == artist_id).all()

  if len(trigger) == 0:
    query_result = item
  else:
    past_shows_query = db.session.query(Show, Venue).join(Venue).filter(Show.artist_id == artist_id).filter(
      Show.start_time < datetime.now()).all()

    for show in past_shows_query:
      past_shows.append(
        {
          "venue_id": show.Show.venue_id,
          "venue_name": show.Venue.name,
          "venue_image_link": show.Venue.image_link,
          "start_time": show.Show.start_time
        }
      )

    upcoming_shows_query = db.session.query(Show, Venue).join(Venue).filter(Show.artist_id == artist_id).filter(
    Show.start_time > datetime.now()).all()

    for show in upcoming_shows_query:
      upcoming_shows.append(
        {
          "venue_id": show.Show.venue_id,
          "venue_name": show.Venue.name,
          "venue_image_link": show.Venue.image_link,
          "start_time": show.Show.start_time
        }
      )
    
    item['past_shows_count'] = len(past_shows)
    item['upcoming_shows_count'] = len(upcoming_shows)

    query_result = item

  return render_template('pages/show_artist.html', artist=query_result)

#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.facebook_link.data = artist.facebook_link
  form.website_link.data = artist.website_link
  form.image_link.data = artist.image_link
  form.genres.data = artist.genres.split(',')
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  try:
    artist = Artist.query.get(artist_id)
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = ','.join(form.genres.data)
    artist.facebook_link = form.facebook_link.data
    artist.image_link = form.image_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data

    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be update.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.address.data = venue.address
  form.facebook_link.data = venue.facebook_link
  form.website_link.data = venue.website_link
  form.image_link.data = venue.image_link
  form.genres.data = venue.genres.split(',')
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  try:
    venue = Venue.query.get(venue_id)
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.address = form.address.data
    venue.genres = ','.join(form.genres.data)
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be update.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  if form.validate():
    try:
      artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = ','.join(form.genres.data),
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )

      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
      flash('Errors: ' + str(message[0]))
      return render_template('forms/new_artist.html', form=form)  
  return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  results = []
  data = Show.query.all()
  for el in data:
    item = {
      'venue_id': el.venue_id,
      'venue_name': db.session.query(Venue.name).filter(Venue.id == el.venue_id).first()[0],
      'artist_id': el.artist_id,
      'artist_name': db.session.query(Artist.name).filter(Artist.id == el.artist_id).first()[0],
      'artist_image_link': db.session.query(Artist.image_link).filter(Artist.id == el.artist_id).first()[0],
      'start_time': el.start_time
    }
    results.append(item)
  return render_template('pages/shows.html', shows=results)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/search', methods=['POST'])
def search_shows():
  searched = request.form.get('search_term')
  response = db.session.query(Artist).filter(
    Artist.name.ilike('%{}%'.format(searched))).all()
  return render_template('pages/show.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  try:
    show = Show(
      artist_id = form.artist_id.data,
      venue_id = form.venue_id.data,
      start_time = form.start_time.data
    )

    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    # on successful db insert, flash success
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

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
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''