import random
from flask import Blueprint, flash, redirect, request, render_template, url_for
from flask_login import current_user, login_required
from . import db
from .auth import provider_permission, seeker_permission
from .forms import CollectiveForm, SearchForm, ProfileForm
from .model import Collective, SeekerProfile
from .images import save_image, delete_picture
from flask import Blueprint


bp = Blueprint('logic', __name__)


# ------------------ ROUTES FOR ALL USERS --------------- #

@bp.route("/", methods=['GET'])
def landing():
  """
  Landing page for all visitors. 
  Shows selected collectives as advertisement. 
  
  Returns:
    str: The landing page
  """
  # Selects 3 random collectives from the database, or fewer if there are less than 3 available.
  # Future iterations could make this based on more dynamic criteria, e.g sponsored adds or a recommender system.
  all_entries = Collective.get_all()
  selected_entries = random.sample(all_entries, min(3, len(all_entries)))
  
  return render_template("landingpage.html", selected_entries=selected_entries)


@bp.route("/collectives", methods=["GET"])
def collectives_index():
    """
    The page for showing the overview of all collectives.
    Allows filtering by city, roomsize and price throught the SearchForm.

    Returns:
        str: The overview page
    """
    form = SearchForm(formdata=request.args)
       
    # if any arguments is given to URL, filter the collectives
    if (request.args):
       collective_entries = Collective.get_by_filters(
           form.city.data,
           form.roomsize.data,
           form.price.data 
        )
    else:
       collective_entries = Collective.get_all()
      
    return render_template("collectives/index.html", collective_entries=collective_entries, form=form)


@bp.route("/collectives/<int:id>", methods=["GET"])
def collectives_view(id):
    """
    The page for a specific collective.

    Args:
        id (int): The id of the collective

    Returns:
        str: The collective page
    """
    entry = Collective.get_by_id(id)
    return render_template("collectives/view.html", entry=entry)


# ------------------ ROUTES FOR SEEKERS --------------- #

@bp.route("/profile", methods=["GET"])
@login_required
@seeker_permission.require()
def profile():
    """
    The seeker's profile page.

    Returns:
        str: The profile page.
    """
    profile = SeekerProfile.get_by_user_id(current_user.id)
    
    form = ProfileForm(obj=profile)
    
    return render_template("profiles/seeker.html", form=form, profile=profile)
  
  
@bp.route("/profile", methods=["POST"])
@login_required
@seeker_permission.require()
def create_or_update_profile():
    """
    Creates the seeker's profile with the provided form data if they don't have one yet.
    Otherwise updates their profile by replacing current data with the new data.
    Method is POST because forms cannot send PUT requests.
    
    Returns:
        The profile page.
    """
    form = ProfileForm()
    profile = SeekerProfile.get_by_user_id(current_user.id)

    if form.validate():
        # Get data from form
        name = form.name.data
        description = form.description.data
        birthdate = form.birthdate.data
        gender = form.gender.data
        occupation = form.occupation.data
        # Save image if it exists
        filename = None
        if form.image.data:
            filename = save_image(form.image.data)

        if profile:
            # Replace current profile with provided information
            profile.replace_all_fields(name, description, birthdate, gender, occupation, filename)
        else:
            # Create profile with provided information
            profile = SeekerProfile.create_seekerprofile(current_user.id, name, description, birthdate, gender, occupation, filename)
      
        flash("Profile saved!", "success")
        return redirect(url_for("logic.profile"))
    else:
        # Reload site with the form data so user doesn't have to start all over if they input something invalid
        flash("Invalid input", "error")
        return render_template("profiles/seeker.html", form=form, profile=profile)



# ------------------ ROUTES FOR PROVIDERS --------------- #

@bp.route("/provider/collectives",methods=["GET", "POST"])
@login_required
@provider_permission.require()
def provider_collectives():
    """
    The provider's 'profile' page showing their collectives on the site.

    Returns:
        str: The page of the provider's collectives.
    """
    collective_entries = Collective.get_by_submitter(current_user.id)
    return render_template("profiles/provider.html", collective_entries=collective_entries)


@bp.route("/collectives/create", methods=["GET", "POST"])
@login_required
@provider_permission.require()
def collectives_create():
    """
    The page for creating new collectives.
    - On POST requests creates the new collective and redirects
    - On GET request renders the collective creation page.

    Returns:
        Response | str: Redirect or the collective creation page.
    """
    form = CollectiveForm()

    if form.validate_on_submit():
        Collective.create_collective(
            current_user.id, 
            form.city.data,
            form.street.data,
            form.roomsize.data,
            form.price.data,
            form.description.data,
            save_image(form.image.data)
            )
        return redirect(url_for("logic.provider_collectives"))
    
    return render_template("collectives/create.html", form=form)


@bp.route("/collectives/delete/<int:id>", methods=["POST"])
@login_required
@provider_permission.require()
def collectives_delete(id):
    """
    Deletes a collective entry. 
    Method is POST because forms cannot send DELETE requests. 

    Args:
        id (int): Id of the collective to delete

    Returns:
        Response: Redirect to provider's overview of their collectives
    """
    entry = Collective.get_by_id(id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        delete_picture(entry.image)
        flash("Collective deleted.","success")
    else:
       flash("Sorry, we couldn't find the collective that you wanted to delete.", 'warning')
       
    return redirect(url_for('logic.provider_collectives'))
 