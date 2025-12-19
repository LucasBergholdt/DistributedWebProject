from flask import Blueprint, flash, redirect, request, render_template, url_for
from flask_login import current_user, login_required

from . import db
from .auth import provider_permission, seeker_permission
from .forms import ProfileForm, CollectiveForm, SearchForm
from .model import Collective, SeekerProfile
from .images import save_image, delete_picture


from flask import Blueprint


bp = Blueprint('logic', __name__)

# ------------------ ANONYMOUS --------------- #
@bp.route("/collectives", methods=["GET"])
def collectives_index():
    form = SearchForm(formdata=request.args)
       
    # if any arguments is given to URL
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
    entry = Collective.get_by_id(id)
    return render_template("collectives/view.html", entry=entry)


# --------------- SEEKER ------------- #

@bp.route("/profile",methods=["GET"])
@login_required
@seeker_permission.require()
def profile():
    profile = SeekerProfile.get_by_user_id(current_user.id)
    
    form = ProfileForm(obj=profile)
    
    return render_template("profiles/seeker.html", form=form, profile=profile)
  
@bp.route("/profile",methods=["POST"])
@login_required
@seeker_permission.require()
def put_profile():
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

# --------------- PROVIDER ----------------- #

@bp.route("/provider/collectives",methods=["GET","POST"])
@login_required
@provider_permission.require()
def provider_collectives():
    collective_entries = Collective.get_by_submitter(current_user.id)
  
    # Get all applications mapped to these collectives.
    #application_entries = [
    #  application
    #  for collective in collective_entries
    #    for application in collective.applications  #relationship() anvendes.
    #]
    return render_template("profiles/provider.html", collective_entries=collective_entries)

@bp.route("/collectives/create", methods=["GET", "POST"])
@login_required
@provider_permission.require()
def collectives_create():
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

# TODO: SKAL DENNE IKKE VÆRE MED PROVIDER PERMISSION ??
@bp.route("/collectives/delete/<int:id>", methods=["POST"])
def collectives_delete(id):
    """ 
    Deletes a collective entry. Method is POST because HTML cannot send DELETE requests. 
    """
    entry = Collective.get_by_id(id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        delete_picture(entry.image)

        #TODO: Delete corresponding picture in database.
        flash("Collective deleted.","success")
    else:
       flash("Sorry, we couldn't find the collective that you wanted to delete.", 'warning')
    return redirect(url_for('logic.provider_collectives'))
 