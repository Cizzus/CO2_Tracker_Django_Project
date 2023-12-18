import datetime
import os
from datetime import date
import requests
from collections import defaultdict
import pandas as pd
import plotly.express as px
from plotly.offline import plot
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import User, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm, FoodCO2Form
from .models import TravelCO2, FoodCO2, EnergyCO2, GlobalCO2Level, Transport, TransportType, EnergyType, Location

RAPID_API_KEY = os.getenv("RAPID_API_KEY")


############################ VIEWS ###################################################

def index(request):
    """
    Function creates home page view. Function checks if last records in the database corresponds
    to the date two days ago (time delay interval in the global CO2 database). If dates do not match
    data is renewed. Lastly, graph of global CO2 level is generated and send into HTML page.
    :param request: HTTP request from the page
    :return: renders the 'index.html' template, passing the generated graph div as context.
    """

    date_update = date.today() + datetime.timedelta(days=-2)
    if GlobalCO2Level.objects.last().date != str(date_update):
        global_co2_level()  # Update global CO2 level database
    graph = generate_co2_global_graph()  # Generates plotly graph
    plot_div = plot(graph, output_type="div", include_plotlyjs=False)  # Generates HTML 'div' of the Plotly graph
    #  'include_plotlyjs=False' parameter indicates not to include the
    #  Plotly JavaScript library, assuming it's already included in the template.
    return render(request, "index.html", {"graph": plot_div})


def your_footprint(request):
    """
    Function calculates CO2 kg emission user parameters, like, Total CO2 kg, CO2 kg emission current week,
    CO2 kg emission by categories. Generates graph with total CO2 kg emission by user.
    :param request: HTTP request from the page
    :return: renders the 'your_footprint.html' template, passing user CO2 kg emission parameters and graph.
    """

    week_limit = 800  # User week CO2 kg emission limit
    # CO2 from Travel
    user_travel_co2 = TravelCO2.objects.filter(user=request.user)
    travel_co2_kg = [float(travel.co2_kg) for travel in user_travel_co2]
    travel_date = [travel.date_created for travel in user_travel_co2]
    travel_co2_sum = round(sum(travel_co2_kg), 2)

    # CO2 from Food
    user_food_co2 = FoodCO2.objects.filter(user=request.user)
    food_co2_kg = [float(food.co2_kg) for food in user_food_co2]
    food_date = [food.date_created for food in user_food_co2]
    food_co2_sum = round(sum(food_co2_kg), 2)

    # CO2 from Energy
    user_energy_co2 = EnergyCO2.objects.filter(user=request.user)
    energy_co2_kg = [float(energy.co2_kg) for energy in user_energy_co2]
    energy_date = [energy.date_created for energy in user_energy_co2]
    energy_co2_sum = round(sum(energy_co2_kg), 2)

    # Total CO2 by user
    total_co2_kg = travel_co2_kg + food_co2_kg + energy_co2_kg
    total_co2_date = travel_date + food_date + energy_date
    # If user have any CO2 emission data
    if total_co2_date:
        total_co2_kg_sum = round(sum(total_co2_kg), 2)
        plot_div = total_user_co2_kg(total_co2_kg, total_co2_date)  # Generates total CO2 kg graph

        # Total week CO2 by user
        total_week_co2_percentage, total_week_co2_kg = week_co2_emission(request.user, week_limit)
        total_week_co2_percentage = round(total_week_co2_percentage, 1)
        total_week_co2_kg = round(total_week_co2_kg, 2)

        # Total CO2 user added by categories
        travel_over_total = round(travel_co2_sum / total_co2_kg_sum * 100, 1)
        food_over_total = round(food_co2_sum / total_co2_kg_sum * 100, 1)
        energy_over_total = round(energy_co2_sum / total_co2_kg_sum * 100, 1)

    # If user do not have any CO2 emission data
    else:
        total_week_co2_percentage = 0
        total_week_co2_kg = 0
        total_co2_kg_sum = 0
        plot_div = None
        travel_over_total = 0
        food_over_total = 0
        energy_over_total = 0

    context = {
        "total_week_co2_percentage": total_week_co2_percentage,
        "total_week_co2_kg": total_week_co2_kg,
        "total_co2_kg": total_co2_kg_sum,
        "week_limit": week_limit,
        "graph": plot_div,
        "travel_over_total": travel_over_total,
        "food_over_total": food_over_total,
        "energy_over_total": energy_over_total,
        "travel_total": travel_co2_sum,
        "food_total": food_co2_sum,
        "energy_total": energy_co2_sum
    }

    return render(request, "your_footprint.html", context=context)


def add_footprint(request):
    """
    Function takes travel, food, energy CO2 emission data of user that is logged in and sends it into
    'add_footprint.html' template.
    :param request: HTTP request from the page
    :return: renders the 'add_footprint.html' template, passing user travel, food, energy CO2 kg emission data.
    """

    context = {
        "travel_co2": TravelCO2.objects.filter(user=request.user).order_by("-date_created"),
        "food_co2": FoodCO2.objects.filter(user=request.user).order_by("-date_created"),
        "energy_co2": EnergyCO2.objects.filter(user=request.user).order_by("-date_created")
    }

    return render(request, "add_footprint.html", context=context)


def energy_co2(request):
    """
    Function takes user inputs from 'energy_co2.html' template and creates EnergyCO2 object which is saved
    in the database. CO2 Kg is calculated from the given 'traditional_energy' or 'clean_energy' functions which API is
    found: https://rapidapi.com/zyla-labs-zyla-labs-default/api/tracker-for-carbon-footprint-api
    :param request: HTTP request from the page
    :return: Saves EnergyCO2 object with given user data and redirects into 'add_footprint.html'
    """

    clean_energy_types = [obj.name for obj in EnergyType.objects.all()]
    locations = [obj.name for obj in Location.objects.all()]
    if request.method == "POST":
        energy_type = request.POST.get("energyType")
        if energy_type == "Traditional":
            location = request.POST.get("location")
            kwh_used = request.POST.get("kwhTraditional")
            date_created = request.POST.get("date_created_label")
            co2_kg = traditional_energy(location, kwh_used)

            EnergyCO2.objects.create(
                user=request.user,
                type=energy_type,
                location=location,
                amount_kwh=kwh_used,
                co2_kg=co2_kg,
                date_created=date_created
            )
            messages.info(request,
                          f"{co2_kg} kg CO2 from {energy_type} energy, {kwh_used} kWh in {location} added "
                          f"successfully.")
            return redirect("add_footprint")

        elif energy_type == "Clean":
            clean_type = request.POST.get("energySource")
            kwh_used = request.POST.get("kwhClean")
            date_created = request.POST.get("date_created_label")
            co2_kg = clean_energy(clean_type, kwh_used)

            EnergyCO2.objects.create(
                user=request.user,
                type=energy_type,
                green_type=clean_type,
                amount_kwh=kwh_used,
                co2_kg=co2_kg,
                date_created=date_created
            )
            messages.info(request,
                          f"{co2_kg} kg CO2 from {energy_type} {clean_type} energy, {kwh_used} kWh, added "
                          f"successfully.")
            return redirect("add_footprint")

    context = {
        "clean_energy_types": clean_energy_types,
        "locations": locations,
        "today": datetime.date.today().strftime("%Y-%m-%d"),
    }

    return render(request, "energy_co2.html", context=context)


def energy_delete(request, pk):
    """
    In the page 'Add footprint' this function gives ability to user to delete his energy CO2 emission records.
    :param request: HTTP request from the page
    :param pk: primary key of EnergyCO2 record
    :return: After successful deletion of the record redirects into 'add_footprint.html' page
    """
    energy = get_object_or_404(EnergyCO2, pk=pk)
    if request.method == "POST":
        energy.delete()
        messages.info(request, message=f"({energy}) deleted successfully.")
        return redirect("add_footprint")
    else:
        return render(request, "add_footprint.html")


def food_co2(request):
    """
    Function processes a form where user can give a food name and its amount, then CO2 kg footprint
    is calculated for every product found from API ('get_food'). API gives how much CO2/kg is
    emitted from given 1 kg of food. If no food from given name is found error message is printed in the
    HTML page. If search is successful, data is rendered into 'food_co2.html' template.
    :param request: HTTP request from the page
    :return: If search result successful, renders data into 'food_co2.html' template. Otherwise, redirects back
    into 'food_co2.html' search page. Also renders form of 'FoodCO2Form' into 'food_co2.html' template
    """

    form = FoodCO2Form()
    if request.method == "POST":
        form = FoodCO2Form(request.POST)
        if form.is_valid():
            food_name = form.cleaned_data["name"]
            amount_kg = form.cleaned_data["amount_kg"]
            date_created = form.cleaned_data["date_created"]
            food_data = get_food(food_name)

            if food_data.text != "Nothing corresponds to the parameter you gave. Please try something else.":
                updated_data = []
                for data in food_data.json():
                    footprint_calc = float(data["footprint"]) * float(amount_kg)
                    data.update({"footprint": round(footprint_calc, 3)})
                    updated_data.append(data)

                context = {
                    "form": form,
                    "food_data": updated_data,
                    "amount_kg": amount_kg,
                    "date_created": date_created
                }

                return render(request, "food_co2.html", context=context)
            else:
                messages.error(request, "Data not found.")
                return redirect("food_co2")

    return render(request, "food_co2.html", {"form": form})


def save_food(request):
    """
    This function saves selected food row in 'food_co2.html' search result table. Row with data is saved
    into database (FoodCO2 model).
    :param request: HTTP request from the page.
    :return: After saving the object redirects from 'food_co2.html' into 'add_footprint.html' page
    """

    group = request.POST.get("group")
    category = request.POST.get("category")
    name = request.POST.get("name")
    amount_kg = request.POST.get("amount_kg")
    footprint = request.POST.get("footprint")

    FoodCO2.objects.create(
        user=request.user,
        group=group,
        category=category,
        name=name,
        amount_kg=amount_kg,
        co2_kg=footprint
    )

    messages.info(request, message=f"Food {name}, {amount_kg} kg, CO2 {footprint} kg added.")

    return redirect("add_footprint")


def food_delete(request, pk):
    """
    In the page 'Add footprint' this function gives ability to user to delete his food CO2 emission records.
    :param request: HTTP request from the page.
    :param pk: primary key of selected record
    :return: After deletion returns into 'add_footprint.html' page.
    """
    food = get_object_or_404(FoodCO2, pk=pk)
    if request.method == "POST":
        food.delete()
        messages.info(request, message=f"({food}) deleted successfully.")
        return redirect("add_footprint")
    else:
        return render(request, "add_footprint.html")


def travel_co2(request):
    """
    Function add travel CO2 emission in the database when user submits transport, transport_type and distance
    in the travel_co2.html page.
    :param request: HTTP request from the page.
    :return: After user clicks "Add CO2" data is sent into function and add travel into CO2 Travel database.
    """
    transport = request.POST.get("transportType")
    # CO2 from Car
    if transport == "CarbonFootprintFromCarTravel":
        car_type = request.POST.get("car_type")
        distance_km = request.POST.get("distance_km")
        co2_kg = co2_from_travel(transport, distance_km, transport_type=car_type)
        date_created = request.POST.get("date_created_label")
        TravelCO2.objects.create(
            user=request.user,
            transport=Transport.objects.get(name="Car"),
            transport_type=TransportType.objects.get(name=car_type),
            distance=distance_km,
            co2_kg=co2_kg,
            date_created=date_created
        )
        messages.info(request,
                      f"{co2_kg} kg CO2 from travel with {car_type} {distance_km} km, added "
                      f"successfully.")
        return redirect("add_footprint")

    # CO2 from Flights
    elif transport == "CarbonFootprintFromFlight":
        plane_type = request.POST.get("planeType")
        distance_km = request.POST.get("distance_km")
        co2_kg = co2_from_travel(transport, distance_km, transport_type=plane_type)
        date_created = request.POST.get("date_created_label")
        TravelCO2.objects.create(
            user=request.user,
            transport=Transport.objects.get(name="Plane"),
            transport_type=TransportType.objects.get(name=plane_type),
            distance=distance_km,
            co2_kg=co2_kg,
            date_created=date_created
        )
        messages.info(request,
                      f"{co2_kg} kg CO2 from travel with {plane_type} {distance_km} km, added "
                      f"successfully.")
        return redirect("add_footprint")

    # CO2 from Motorbikes
    elif transport == "CarbonFootprintFromMotorBike":
        moto_type = request.POST.get("motorbikeType")
        distance_km = request.POST.get("distance_km")
        date_created = request.POST.get("date_created_label")
        co2_kg = co2_from_travel(transport, distance_km, transport_type=moto_type)
        TravelCO2.objects.create(
            user=request.user,
            transport=Transport.objects.get(name="Motorbike"),
            transport_type=TransportType.objects.get(name=moto_type),
            distance=distance_km,
            co2_kg=co2_kg,
            date_created=date_created
        )
        messages.info(request,
                      f"{co2_kg} kg CO2 from travel with {moto_type} {distance_km} km, added "
                      f"successfully.")
        return redirect("add_footprint")

    # CO2 from Public Transport
    elif transport == "CarbonFootprintFromPublicTransit":
        public_type = request.POST.get("publicTransport")
        distance_km = request.POST.get("distance_km")
        co2_kg = co2_from_travel(transport, distance_km, transport_type=public_type)
        date_created = request.POST.get("date_created_label")
        TravelCO2.objects.create(
            user=request.user,
            transport=Transport.objects.get(name="Public transport"),
            transport_type=TransportType.objects.get(name=public_type),
            distance=distance_km,
            co2_kg=co2_kg,
            date_created=date_created
        )

        messages.info(request,
                      f"{co2_kg} kg CO2 from travel with {public_type} {distance_km} km, added "
                      f"successfully.")
        return redirect("add_footprint")

    # Types of transport given from the transport_types function
    car_types, motorbike_types, plane_types, public_transport_types = transport_types()

    context = {
        "car_types": car_types,
        "motorbike_types": motorbike_types,
        "plane_types": plane_types,
        "public_transport_types": public_transport_types,
        "today": datetime.date.today().strftime("%Y-%m-%d")
    }

    return render(request, "travel_co2.html", context=context)


def travel_delete(request, pk):
    """
    FUnction gives ability for the users to delete footprint records they added.
    :param request: HTTP request from the page.
    :param pk: primary key of the particular footprint record
    :return: If the user clicks delete, record is deleted and user 'add footprint' page reloads
    """
    travel = get_object_or_404(TravelCO2, pk=pk)
    if request.method == "POST":
        travel.delete()
        messages.info(request, message=f"({travel}) deleted successfully.")
        return redirect("add_footprint")
    else:
        return render(request, "add_footprint.html")


def footprint_highscore(request):
    """
    Functions calculates users average CO2 kg / day emission and depicts it in the table. Table is rendered
    into 'footprint_highscore.html' template.
    :param request: HTTP request from the page.
    :return: Renders users CO2 kg emission table into 'footprint_highscore.html' .
    """
    all_users = User.objects.all()
    users = []
    avg_co2_kg = []
    for user in all_users:
        # Extracts CO2 kg emission by user
        all_footprints = []
        travel_co2_obj = TravelCO2.objects.filter(user=user)
        food_co2_obj = FoodCO2.objects.filter(user=user)
        energy_co2_obj = EnergyCO2.objects.filter(user=user)
        all_footprints += travel_co2_obj
        all_footprints += food_co2_obj
        all_footprints += energy_co2_obj
        # If user has any footprint records then it is calculated for highscore table
        if all_footprints:
            # Calculates total CO2 kg emission of particular user
            co2_kg = 0
            dates = []
            for footprint in all_footprints:
                co2_kg += footprint.co2_kg
                dates.append(footprint.date_created)
            # Calculates average CO2 kg emission / day of particular user
            avg_co2_kg_user = co2_kg / len(set(dates))
            # Puts username and CO2 kg/day into particular list
            users.append(user.username)
            avg_co2_kg.append(round(avg_co2_kg_user, 2))
    # Prepare and puts all data into pandas DataFrame HTML table
    data = {
        "Username": users,
        "Average CO2 (kg/day) emission": avg_co2_kg
    }
    df = pd.DataFrame(data)
    df_html = df.to_html(classes="table", table_id="highscore_table", index=False)

    return render(request, "footprint_highscore.html", context={"df_html": df_html})


@csrf_protect
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password2 = request.POST["password2"]

        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username {username} already exist!")
                return redirect("register")
            else:
                if User.objects.filter(email=email).exists():
                    messages.error(request, f"User email {email} already exist!")
                    return redirect("register")
                else:
                    User.objects.create_user(username=username, email=email, password=password)
                    messages.info(request, f"User {username} registered successfully!")
                    return redirect("login")
        else:
            messages.error(request, "Passwords do not match!")
            return redirect("register")
    return render(request, "register.html")


@login_required
def change_password(request):
    if request.method == "POST":
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.info(request, f"Profile password updated")
            return redirect("your_footprint")
    else:
        password_form = PasswordChangeForm(request.user)

    context = {
        "password_form": password_form
    }
    return render(request, "change_password.html", context=context)


@login_required
def profile(request):
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.info(request, f"Profile Updated")
            return redirect("profile")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        "u_form": u_form,
        "p_form": p_form,
    }
    return render(request, "profile.html", context=context)


####################### VIEWS FUNCTIONS ############################

def global_co2_level():
    """
    Function sends request into https://rapidapi.com/rene-mdd/api/daily-atmosphere-carbon-dioxide-concentration/
    API to retrieve global CO2 kg emission data and save it into database.
    """
    # Making API request
    url = "https://daily-atmosphere-carbon-dioxide-concentration.p.rapidapi.com/api/co2-api"

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "daily-atmosphere-carbon-dioxide-concentration.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    if response.ok:
        # Clear existing data in the database
        GlobalCO2Level.objects.all().delete()

        # Extracting new global CO2 emission data and saving into database
        objects_list = []
        for data_point in response.json()["co2"]:
            year = data_point["year"]
            month = data_point["month"]
            if len(month) == 1:
                month = "0" + month
            day = data_point["day"]
            if len(day) == 1:
                day = "0" + day
            cycle = float(data_point["cycle"])
            trend = float(data_point["trend"])
            date_form = f"{year}-{month}-{day}"
            objects_list.append(GlobalCO2Level(date=date_form, trend=trend, cycle=cycle))
        # Saves all appended GlobalCO2Level objects into database
        GlobalCO2Level.objects.bulk_create(objects_list)


def generate_co2_global_graph():
    """
    Function generates plotly interactive graph of the Global CO2 emission.
    :return: plotly figure of the global CO2 emission.
    """
    date_ = [obj.date for obj in GlobalCO2Level.objects.all()]
    trend = [obj.trend for obj in GlobalCO2Level.objects.all()]
    cycle = [obj.cycle for obj in GlobalCO2Level.objects.all()]
    data = {"date": date_, "trend": trend, "cycle": cycle}
    fig = px.line(data, x="date", y=["trend", "cycle"], line_shape="linear")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="CO<sub>2</sub>, ppm",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1.0
        ),
        legend_title_text="",
        plot_bgcolor="white",
        paper_bgcolor="rgba(256,256,256,0)",
        font=dict(
            size=20,
            color="black"
        )
    )
    fig.update_traces(
        name="Trend*",
        selector=dict(name="trend")
    )
    fig.update_traces(
        name="Cycle**",
        selector=dict(name="cycle")
    )
    fig.update_xaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey"
    )
    fig.update_yaxes(
        mirror=True,
        ticks="outside",
        showline=True,
        linecolor="black",
        gridcolor="lightgrey"
    )

    return fig


def generate_total_co2_graph(co2_kg: list, co2_dates: list):
    """
    For the given data - CO2 kg and date of the CO2 footprint - creates an interactive plotly graph.
    :param co2_kg: List of float CO2 kg emission values
    :param co2_dates: List of CO2 kg emission dates
    :return: Plotly graph of CO2 emission dates vs. CO2 kg emission
    """
    data = {"date": co2_dates, "co2_kg": co2_kg}
    data_df = pd.DataFrame(data).sort_values("date")
    fig = px.line(data_df, x="date", y="co2_kg", line_shape="linear", markers=True)
    fig.update_traces(line=dict(width=4.0))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=r"CO<sub>2</sub>, <i>kg</i>",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1),
        xaxis=dict(
            tickmode="linear",
            tickformat="%Y-%m-%d",
            tickangle=45
        ),
        plot_bgcolor="rgba(128, 128,128,1)",
        paper_bgcolor="rgba(256,256,256,0)",
        font=dict(
            family="Calibri",
            size=24,
            color="Black"
        )

    )
    week_ago = datetime.date.today() + datetime.timedelta(-7)
    fig.update_xaxes(tickfont_size=14, range=[week_ago, datetime.date.today()])
    fig.update_traces(marker=dict(size=12, color="darkblue"))

    return fig


def co2_from_travel(transport: str, distance: str, transport_type: str):
    """
    Calculates CO2 kg emission from the given transport (e.g., 'Car', 'Plane'), transport type (e.g., 'Small Diesel
    Car') and distance in km. CO2 in kg is sent from API:
     https://rapidapi.com/carbonandmore-carbonandmore-default/api/carbonfootprint1/
    :param transport: API name for particular transport, e.g. for car - "CarbonFootprintFromCarTravel"
    :param distance: Distance completed in km.
    :param transport_type: Name of transport type from API documentation, e.g. for car - "MediumDieselCar"
    :return: String value of CO2 kg emission for given transport
    """

    url = f"https://carbonfootprint1.p.rapidapi.com/{transport}"
    trans_type = transport_type.replace(" ", "")
    if transport.find('Car', 3) != -1:
        # Parameters for car travel requests
        querystring = {"distance": distance, "vehicle": trans_type}
    else:
        # Parameters for plane, motorbike, or public transport requests
        querystring = {"distance": distance, "type": trans_type}

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "carbonfootprint1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    co2_kg = response.json()["carbonEquivalent"]

    return co2_kg


def transport_types():
    """
    Function returns types of 4 transports ("Car", "Motorbike", "Plane", "Public Transport", in respective order)
    from Django Transport types table.
    :return: 4 lists of transport types.
    """

    all_types = TransportType.objects.all()
    car_types = []
    motorbike_types = []
    plane_types = []
    public_transport_types = []
    for type_ in all_types:
        if str(type_.transport) == "Car":
            car_types.append(type_.name)
        elif str(type_.transport) == "Plane":
            plane_types.append(type_.name)
        elif str(type_.transport) == "Motorbike":
            motorbike_types.append(type_.name)
        elif str(type_.transport) == "Public transport":
            public_transport_types.append(type_.name)

    return car_types, motorbike_types, plane_types, public_transport_types


def week_co2_emission(user, week_limit: float):
    """
    Function calculates total CO2 kg emitted for particular user in the current week.
    :param user: User object from django database.
    :param week_limit: Float value of week CO2 kg limit.
    :return: two float objects, first - percentage of CO2 kg emitted current week, second - total CO2 kg emitted current
    week.
    """
    today = datetime.datetime.today()
    year, week_num, day_of_week = today.isocalendar()

    # Load Django database objects for particular user
    travel_co2_objs = TravelCO2.objects.filter(user=user, date_created__week=week_num)
    food_co2_objs = FoodCO2.objects.filter(user=user, date_created__week=week_num)
    energy_co2_objs = EnergyCO2.objects.filter(user=user, date_created__week=week_num)
    all_data_objs = list(travel_co2_objs) + list(food_co2_objs) + list(energy_co2_objs)

    # Calculate proportion of CO2 kg emitted current week compared to week limit and total CO2 kg emitted current week
    total_co2_kg = [float(obj.co2_kg) for obj in all_data_objs]
    total_co2_percentage = sum(total_co2_kg) / week_limit * 100
    total_co2 = sum(total_co2_kg)
    return total_co2_percentage, total_co2


def traditional_energy(location: str, kwh_used: str):
    """
    Function calculates CO2 kg emission by traditional energy used in particular region (location, e.g. Lithuania) and
    amount of energy (KWH) used. CO2 kg emission is given from API:
    https://rapidapi.com/carbonsutra/api/carbonsutra1/
    :param location: String value of region where traditional energy used.
    :param kwh_used: String value of amount of energy used in KWH
    :return: string value of kg CO2 emitted from energy used in particular region and amount.
    """

    url = "https://carbonsutra1.p.rapidapi.com/electricity_estimate"

    payload = {
        "country_name": location,
        "electricity_value": kwh_used,
        "electricity_unit": "kWh"
    }
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "Authorization": "Bearer fQ98oU704xFvsnXcQLVDbpeCJHPglG1DcxiMLKfpeNEMGumlbzVf1lCI6ZBx",
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "carbonsutra1.p.rapidapi.com"
    }

    response = requests.post(url, data=payload, headers=headers)

    co2_kg = response.json()["data"]["co2e_kg"]
    return co2_kg


def clean_energy(type_of_energy: str, consumption: str):
    """
    Function calculates CO2 kg emission by clean energy used from particular energy type (e.g. Solar) and
    amount of energy (KWH) used (consumption). CO2 kg emission is given from API:
    https://rapidapi.com/zyla-labs-zyla-labs-default/api/tracker-for-carbon-footprint-api/
    :param type_of_energy: String value of energy source name found in API documentation.
    :param consumption:  String value of amount KWH used from particular clean energy source
    :return: string value of kg CO2 kg emitted from energy used from particular clean energy source and amount.
    """
    url = "https://tracker-for-carbon-footprint-api.p.rapidapi.com/cleanHydro"

    payload = {
        "energy": type_of_energy,
        "consumption": consumption
    }
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tracker-for-carbon-footprint-api.p.rapidapi.com"
    }

    response = requests.post(url, data=payload, headers=headers)
    if response.ok:
        kg_co2 = response.json()["carbon"]
        kg_co2 = kg_co2.replace("kg co2", "")
        return kg_co2


def total_user_co2_kg(total_co2_kg: list, total_co2_date: list):
    """
    Function from list of CO2 kg emission and date list which corresponds to respective CO2 emission in CO2 kg emission
    list generates two list where first list contain total CO2 kg for every date in other list. From total CO2 kg
    emission and dated line graph is created and returned.
    :param total_co2_kg: List of CO2 kg emitted.
    :param total_co2_date: Dates of total_co2_kg list values created.
    :return: Line graph of total CO2 kg emitted by date.
    """
    # Create list where all dates between earliest and latest dates are filled by day.
    all_dates = pd.date_range(min(total_co2_date), max(total_co2_date), freq="D")
    # Create list of only date values
    all_dates_str = [only_date.date() for only_date in all_dates.to_list()]
    # Create 0 CO2 kg values for all dates
    all_co2_values = [0 for _ in range(len(all_dates_str))]
    # We add user given CO2 kg emission and respective date values of those emissions to list of 0 CO2 values with
    # respective dates
    total_co2_kg += all_co2_values
    total_co2_date += all_dates_str
    data_dict = defaultdict(float)
    # For the given date we add kg of CO2 emitted.
    for date_, kg in zip(total_co2_date, total_co2_kg):
        data_dict[date_] += kg
    # We decompose generated dict into its key ('unique_dates') and value ('total_co2_kg') lists.
    unique_dates, total_co2_kg_ = zip(*data_dict.items())
    graph = generate_total_co2_graph(total_co2_kg_, unique_dates)
    plot_div = plot(graph, output_type="div", include_plotlyjs=False)
    return plot_div


def get_food(food_name: str):
    """
    Function sends request into Foodprint API:
    https://rapidapi.com/benarapovic/api/foodprint/
    API response is composed of food data, like, name of the food, kg of CO2 generated from 1 kg of food, etc.
    :param food_name: string value of food name, for example, 'bread'.
    :return: API response from Foodprint API
    """

    food_name_format = food_name.replace(" ", "%20")
    url = f"https://foodprint.p.rapidapi.com/api/foodprint/name/{food_name_format}"

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "foodprint.p.rapidapi.com"
    }
    food_data = requests.get(url, headers=headers)
    return food_data
