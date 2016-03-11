# room_display
A service to allow easy display of meeting room status from Outlook/Exchange

## Running

The easiest way to run the server is using docker-compose:
```bash
docker-compose up
```
Once the image has finished building & everything is running, you should be able to hit http://192.168.99.100:5000 to view the website.

## Todo

Both:
* Agree data contract

Backend:
* Add makefile?
* Return dummy data
* Retrieve data from exchange
  * Accept username, password & exchange URL as environment variabless
* Periodically poll for new data
  * Accept interval as environment variable
* Accept insta-bookings

Frontend:
* Render overview page
* Render individual page
* Retrieve data from backend
* Periodically poll for new data
* Add home page & move there after inactivity
* Add currently free room suggestions
* Add soonest free room suggestions
* Add insta-bookings
* Theme switching with https://github.com/jguadagno/bootstrapThemeSwitcher

## Credits

The favicon is from [www.iconarchive.com](http://www.iconarchive.com/show/pretty-office-7-icons-by-custom-icon-design/Calendar-icon.html).
