#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import db, Venue, Artist, Shows
import sys
import re
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
# db = SQLAlchemy(app)
db.app = app
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
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
    allVenueData = Venue.query.distinct(Venue.city, Venue.state)
    venuesList = Venue.query.order_by(Venue.id).all()
    return render_template('pages/venues.html', areas=allVenueData, areaVenues=venuesList)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    search_data = str(search_term)
    venues = Venue.query.filter(Venue.name.ilike("%"+search_data+"%")).all()
    venue_list = []
    for search in venues:
        venue_list.append({
            "id": search.id,
            "name": search.name,
            "city": search.city
        })
    response = {
        "count": len(venues),
        "data": venue_list
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    genres = [venue.genres]
    # TODO: replace with real venue data from the venues table, using venue_id
    future_shows = db.session.query(Shows).join(Artist).filter(
        Shows.venue_id == venue_id).filter(Shows.start_time > datetime.now()).all()
    future_shows_array = []

    previous_show = db.session.query(Shows).join(Artist).filter(
        Shows.venue_id == venue_id).filter(Shows.start_time < datetime.now()).all()
    previous_show_array = []

    for show in previous_show:
        previous_show_array.append({
            "artist_id": show['artist_id'],
            "artist_name": show['artist'].name,
            "artist_image_link": show['artist'].image_link,
            "start_time": show['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        })

    for show in future_shows:
        future_shows_array.append({
            "artist_id": show['artist_id'],
            "artist_name": show['artist'].name,
            "artist_image_link": show['artist'].image_link,
            "start_time": show['start_time'].strftime("%Y-%m-%d %H:%M:%S")
        })
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "description": venue.description,
        "image_link": venue.image_link,
        "past_shows": previous_show_array,
        "upcoming_shows": future_shows_array,
        "past_shows_count": len(previous_show_array),
        "upcoming_shows_count": len(future_shows_array),
    }
    # data = list(filter(lambda d: d['id'] ==
    #             venue_id, [data1, data2, data3]))[0]
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
    form = VenueForm(request.form)

    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    description = form.description.data
    genres = form.genres.data
    genres = str(genres)
    genres = re.sub(r"[^a-zA-Z0-9]", " ", genres)
    seeking_talent = True if form.seeking_talent.data else False

    # TODO: modify data to be the data object returned from db insertion

    try:
        newVenue = Venue(name=name, city=city, state=state, address=address, phone=phone,
                         image_link=image_link, facebook_link=facebook_link, website_link=website_link,
                         description=description, seeking_talent=seeking_talent,)
        db.session.add(newVenue)
        db.session.commit()
        error = False
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' +
              form.name.data + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        return render_template('pages/home.html')
    elif not error:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    allArtistsData = Artist.query.order_by(Artist.name).all()
    return render_template('pages/artists.html', artists=allArtistsData)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    search_data = str(search_term)
    artists = Artist.query.filter(Artist.name.ilike("%"+search_data+"%")).all()
    artist_list = []
    for search in artists:
        artist_list.append({
            "id": search.id,
            "name": search.name,
            'total_upcoming_shows': Shows.query.filter(Shows.id == search.id).filter(Shows.start_time > datetime.now()).all(),
        })
    response = {
        "count": len(artists),
        "data": artist_list
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)

    artist_data = artist.to_dict()
    previous_shows = list(filter(lambda x: x.start_time <
                          datetime.today(), artist.shows))
    future_shows = list(filter(lambda x: x.start_time >=
                        datetime.today(), artist.shows))

    previous_shows = list(map(lambda x: x.show_venue(), previous_shows))
    future_shows = list(map(lambda x: x.show_venue(), future_shows))

    artist_data['previous_shows'] = previous_shows
    artist_data['future_shows'] = future_shows
    artist_data['previous_shows_count'] = len(previous_shows)
    artist_data['future_shows_count'] = len(future_shows)
    # data = list(filter(lambda d: d['id'] ==
    #             artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).all()[0]
    state = form.state.default = artist.state
    form.process()
    form = ArtistForm(obj=artist)
    genres = [artist.genres]
    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": genres,
        "city": artist.city,
        "state": state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_description": artist.description,
        "image_link": artist.image_link
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

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
    form = ArtistForm(request.form)

    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    description = form.description.data
    genres = form.genres.data
    genres = str(genres)
    genres = re.sub(r"[^a-zA-Z0-9]", " ", genres)
    looking_for_venues = True if form.seeking_venue.data else False

    # TODO: modify data to be the data object returned from db insertion
    try:
        newArtist = Artist(name=name, city=city, state=state, phone=phone,
                           image_link=image_link, facebook_link=facebook_link, website_link=website_link,
                           looking_for_venues=looking_for_venues, description=description, genres=genres)
        db.session.add(newArtist)
        db.session.commit()
        error = False
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' +
              form.name.data + ' could not be listed.')
        return render_template('pages/home.html')
    elif not error:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    shows = Shows.query.all()
    for i in range(len(shows)):
        artist = Artist.query.with_entities(Artist.id, Artist.name, Artist.image_link).join(
            Shows, Artist.id == Shows.artist_id).filter_by(id=shows[i].id).all()[0]
        venue = Venue.query.with_entities(Venue.id, Venue.name).join(
            Shows, Venue.id == Shows.venue_id).filter_by(id=shows[i].id).all()[0]
        new_show = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": shows[i].start_time
        }
        data.append(new_show)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    artistsList = Artist.query.order_by('id').all()
    venueList = Venue.query.order_by('id').all()
    return render_template('forms/new_show.html', form=form, artistsList=artistsList, venueList=venueList)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    showInfo = ShowForm(request.form)
    artist_id = showInfo.artist_id.data
    venue_id = showInfo.venue_id.data
    start_time = showInfo.start_time.data

    # TODO: insert form data as a new Show record in the db, instead
    try:
        newShow = Shows(start_time=start_time,
                        artist_id=artist_id, venue_id=venue_id)
        db.session.add(newShow)
        db.session.commit()
        error = False
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        # TODO: on unsuccessful db insert, flash an error instead.
        flash(f'Sorry an error occurred.  Show could not be listed. make sure artist and venue id exist')
        print("Error in create_show_submission()")
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        return render_template('pages/home.html')

    elif not error:
        # on successful db insert, flash success
        flash('Show was successfully listed!')
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
