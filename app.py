#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
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
    value = str(value)
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
    venues = Venue.query.all()
    all_venue_data = Venue.query.distinct(Venue.city, Venue.state)
    venues_list = Venue.query.order_by(Venue.id).all()
    print(f"this is venues :: {venues}")
    print(f"this is all_venue_data :: {all_venue_data}")
    print(f"this is venues_list :: {venues_list}")
    return render_template('pages/venues.html', areas=all_venue_data, area_venues=venues_list)
    # return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_query = request.form.get('search_term', '')
    result = Venue.query.filter(Venue.name.ilike(f'%{search_query}%')).all()
    query_data = []

    for item in result:
        query_data.append({
            'id': item.id,
            'name': item.name,
            'image_link': item.image_link,
            'future_show_count': len(db.session.query(Shows).filter(Shows.venue_id == item.id).filter(Shows.start_time > datetime.now()).all())
        })
    response = {
        "count": len(result),
        "data": query_data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    arecords = Artist.query.with_entities(
        Artist.id, Artist.name, Artist.image_link).all()[0]
    genres = [venue.genres]
    future_shows = []
    future_shows_count = 0
    old_shows = []
    old_shows_count = 0
    current_time = datetime.now()
    for show in venue.shows:
        if show.start_time > current_time:
            arecord = arecords
            id = arecord.id
            name = arecord.name
            img_link = arecord.image_link
            future_shows_count += 1
            record = {
                "artist_id": id,
                "artist_name": name,
                "artist_image_link": img_link,
                "start_time": format_datetime(str(show.start_time))
            }
            future_shows.append(record)
        if show.start_time < current_time:
            arecord = arecords
            id = arecord.id
            name = arecord.name
            img_link = arecord.image_link
            old_shows_count += 1
            record = {
                "artist_id": id,
                "artist_name": name,
                "artist_image_link": img_link,
                "start_time": format_datetime(str(show.start_time))
            }
            old_shows.append(record)

    data = {
        "id": venue_id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.description,
        "image_link": venue.image_link,
        "past_shows": old_shows,
        "past_shows_count": old_shows_count,
        "upcoming_shows": future_shows,
        "upcoming_shows_count": future_shows_count
    }

    def Merge(data2, data3):
        res = {**data2, **data3}
        return res
    data2 = {
        "upcoming_shows": future_shows,
        "upcoming_shows_count": future_shows_count
    }
    data3 = {
        "past_shows": old_shows,
        "past_shows_count": old_shows_count
    }
    data_real = Merge(data2, data3)
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
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        error = False
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash(
            f'oopps, an error occurred. Venue {venue_id} could not be deleted.')
    if not error:
        flash(f'Venue {venue_id} was successfully deleted.')
    return render_template('pages/home.html')
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    # return None

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
            "image_link": search.image_link,
            'total_upcoming_shows': Shows.query.filter(Shows.id == search.id).filter(Shows.start_time > datetime.now()).all(),
        })
    response = {
        "count": len(artists),
        "data": artist_list
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#  function converts objects to dictionary


def to_dict(self):
    return json.loads(json.dumps(self, default=lambda o: o.__dict__))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist_profile = Artist.query.get(artist_id)
    vrecords = Venue.query.with_entities(
        Venue.id, Venue.name, Venue.image_link).all()[0]
    future_shows = []
    future_shows_count = 0
    old_shows = []
    old_shows_count = 0
    current_time = datetime.now()
    jazz = [artist_profile.genres]
    for show in artist_profile.shows:
        if show.start_time > current_time:
            vrecord = vrecords
            id = vrecord.id
            name = vrecord.name
            img_link = vrecord.image_link
            future_shows_count += 1
            record = {
                "venue_id": id,
                "venue_name": name,
                "venue_image_link": img_link,
                "start_time": format_datetime(str(show.start_time))
            }
            future_shows.append(record)
        if show.start_time < current_time:
            vrecord = vrecords
            id = vrecord.id
            name = vrecord.name
            img_link = vrecord.image_link
            old_shows_count += 1
            record = {
                "venue_id": id,
                "venue_name": name,
                "venue_image_link": img_link,
                "start_time": format_datetime(str(show.start_time))
            }
            old_shows.append(record)

    def Merge(data1, data2, data3):
        res = {**data1, **data2, **data3}
        return res

    data1 = {
        "id": artist_id,
        "name": artist_profile.name,
        "genres": jazz,
        "city": artist_profile.city,
        "state": artist_profile.state,
        "phone": artist_profile.phone,
        "website": artist_profile.website_link,
        "facebook_link": artist_profile.facebook_link,
        "seeking_venue": artist_profile.looking_for_venues,
        "seeking_description": artist_profile.description,
        "image_link": artist_profile.image_link,
    }
    data2 = {
        "upcoming_shows": future_shows,
        "upcoming_shows_count": future_shows_count
    }
    data3 = {
        "past_shows": old_shows,
        "past_shows_count": old_shows_count,
    }
    data = Merge(data1, data2, data3)

    return render_template('pages/show_artist.html', artist=data)

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
    form = ArtistForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_description = form.seeking_description.data
    genres = form.genres.data
    genres = str(genres)
    genres = re.sub(r"[^a-zA-Z0-9]", " ", genres)
    seeking_venue = True if form.seeking_venue.data else False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.image_link = image_link
        artist.facebook_link = facebook_link
        artist.website_link = website_link
        artist.description = seeking_description
        artist.genres = genres
        artist.looking_for_venues = seeking_venue
        db.session.commit()
        error = False
    except Exception as e:
        error = True
        print(f'Exception "{e}" in edit_venue_submission()')
        db.session.rollback()
    finally:
        db.session.close()
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        flash('An error occurred. Artist ' + name + ' could not be updated.')
        print("Error in edit_venue_submission()")
        print(sys.exc_info())
        abort(500)
    # artist record with ID <artist_id> using the new attributes
    # return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).all()[0]
    state = form.state.default = venue.state
    seeking_talent = form.seeking_talent.default = venue.seeking_talent
    form.process()
    form = VenueForm(obj=venue)
    genres = [venue.genres]
    venue = {
        "id": venue_id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": seeking_talent,
        "seeking_description": venue.description,
        "image_link": venue.image_link
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    form = VenueForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_description = form.seeking_description.data
    genres = form.genres.data
    genres = str(genres)
    genres = re.sub(r"[^a-zA-Z0-9]", " ", genres)
    seeking_talent = True if form.seeking_talent.data else False

    try:
        venue = Venue.query.get(venue_id)
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.image_link = image_link
        venue.facebook_link = form.facebook_link.data
        venue.website_link = website_link
        venue.description = seeking_description
        venue.genres = genres
        venue.seeking_talent = seeking_talent
        db.session.commit()
        error = False
    except Exception as e:
        error = True
        print(f'Exception "{e}" in edit_venue_submission()')
        db.session.rollback()
    finally:
        db.session.close()
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        flash('An error occurred. Venue ' + name + ' could not be updated.')
        print("Error in edit_venue_submission()")
        abort(500)
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
