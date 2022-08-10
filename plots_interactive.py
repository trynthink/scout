#!/usr/bin/env python3

################################################################################
# file: plots_interactive.py
#
# define and run a dash application to allow end users to explore Scout
# diagnostic grpahics interactively.
#
################################################################################

import sys, getopt
import os.path
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import dcc
from dash import html

from plots_utilities import ECM_PREP
from plots_utilities import ECM_RESULTS

################################################################################
# Define the Dash Application
app = dash.Dash(external_stylesheets = [dbc.themes.BOOTSTRAP])

################################################################################
# Define the Dash Application UI

# styling the side bar and contents
sidebar_style = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "24rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
content_style = {
    "margin-left": "26rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# build the sidebar
sidebar = html.Div(
    [
        html.H2("Scout Diagnostic Plots", className="display-4"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Financial Metrics",
                    href="/financial_metrics", active="exact"),
                dbc.NavLink("Cost Effective Savings",
                    href="/cost_effective_savings", active="exact"),
                dbc.NavLink("Total Savings",
                    href="/total_savings", active="exact"),
                dbc.NavLink("Competed vs Uncompeted",
                    href="/cms_v_ums", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=sidebar_style,
)

content = html.Div(id="page-content", style=content_style)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

################################################################################
# App Call Backs

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return home()
    elif pathname == "/financial_metrics":
        return financial_metrics()
    elif pathname == "/cost_effective_savings":
        return cost_effective_savings()
    elif pathname == "/total_savings":
        return total_savings()
    elif pathname == "/cms_v_ums":
        return cms_v_ums()
    # If the user tries to reach a different page, return a 404 message
    return dbc.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised.")
        ]
    )


def home():
    pg = html.Div([
        html.P("A overview of what this application does goes here.")
        ])
    return pg

def financial_metrics():
    pg = html.Div([
        html.H1("Financial Metrics"),
        html.Div([
            html.P("Select Aggregation Level:"),
            dcc.Dropdown(id = "fm_dropdown",
                options = [
                    {"label" : "Aggregated by Year", "value" : "agg_year"},
                    {"label" : "All ECMS", "value" : "all_ecms"},
                    {"label" : "Select an ECM:", "value" : "each_ecm"}
                    ],
                value = "agg_year",
                clearable = False
                )],
            style = {"width" : "25%", "display" : "inline-block"}
            ),
        html.Div([
            html.Label("ECM:"),
            dcc.Dropdown(id = "ecm_dropdown",
                options = ecms,
                value = ecms[0]["value"],
                clearable = False)
            ],
            id = "ecm_dropdown_div",
            style = {"min-width" : "500px", "display" : "none"}),
        html.Div(
            id = "fm-output-container",
            style = {'width' : '90%', 'height': '900px'}
            )
        ])
    return pg

@app.callback(
        Output(component_id = 'ecm_dropdown_div', component_property = "style"),
        Input(component_id = 'fm_dropdown', component_property = 'value')
        )
def show_hide_ecm_dropdown(value):
    if value == "each_ecm":
        return {"display" : "block"}
    else:
        return {"display" : "none"}

@app.callback(
        Output('fm-output-container', 'children'),
        Input('fm_dropdown', 'value'),
        Input('ecm_dropdown', 'value')
        )
def update_fm_output(fm_dropdown_value, ecm_dropdown_value):
    if fm_dropdown_value == "agg_year":
        return dcc.Graph(figure = ecm_results.generate_fm_agg_year())
    elif fm_dropdown_value == "all_ecms":
        return dcc.Graph(figure = ecm_results.generate_fm_by_ecm())
    elif fm_dropdown_value == "each_ecm":
        return dcc.Graph(figure = ecm_results.generate_fm_by_ecm(ecm_dropdown_value))
    else:
        return "impressive, everything you did is wrong"





def cost_effective_savings():
    pg = html.Div([
        html.H1("Cost Effective Savings"),
        html.Div([
            html.Label("Impact:"),
            dcc.Dropdown(id = "ces_cce_dropdown",
                options = [
                    {"label" : "Avoided CO\u2082 Emissions (MMTons)", "value" : "carbon"},
                    {"label" : "Energy Cost Savings (USD)",           "value" : "cost"},
                    {"label" : "Energy Savings (MMBtu)",              "value" : "energy"}
                    ],
                value = "carbon",
                clearable = False
                )],
            style = {"width" : "25%", "display" : "inline-block"}
            ),
        html.Div([
            html.Label("Year:"),
            dcc.Dropdown(id = "year_dropdown", options = years, value = years[0], clearable = False)], id = "ecm_dropdown_div", style = {"min-width" : "500px", "display" : "inline-block"}),
        html.Div(id = "ces-output-container", style = {'width' : '90%', 'height': '900px'})
    ])
    return pg

@app.callback(
        Output('ces-output-container', 'children'),
        Input('ces_cce_dropdown', 'value'),
        Input('year_dropdown', 'value')
        )
def update_ces_output(ces_dropdown_value, year_dropdown_value):
    if ces_dropdown_value == "carbon":
        m = "Avoided CO\u2082 Emissions (MMTons)"
    elif ces_dropdown_value == "cost":
        m = "Energy Cost Savings (USD)"
    elif ces_dropdown_value == "energy":
        m = "Energy Savings (MMBtu)"
    else: 
        m = None
    return dcc.Graph(figure = ecm_results.generate_cost_effective_savings(m = m, year = year_dropdown_value))

def total_savings():
    pg = html.Div([
        html.H1("Total Savings")
        ])
    return pg

def cms_v_ums():
    pg = html.Div([
        html.H1("Competed v Uncompeted")
        ])
    return pg


################################################################################
# Define to do if the file is run directory

# Define some help documentation which will be conditionally shown to the end
# user.
help_usage = "Usage: plots_interactive.py [options]"
help_options = """
Options:
  -h --help          Print this help and exit"
  -d --debug         If present, run the app with debug = True"
  -p --port=N        The port to run the dash app through"
  --ecm_prep=FILE    Path to a ecm_prep.json FILE, the results of ecm_prep.py"
  --ecm_results=FILE Path to a ecm_results.json FILE, the results of run.py"
"""


if __name__ == "__main__":

    # get command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                "hdp:", ["help", "debug", "port=", "ecm_results=", "ecm_prep="])
    except getopt.GetoptError:
        print(help_usage)
        print("Get more details by running: plots_interactive.py -h")
        sys.exit(2)

    # set default values for command line arguments
    ecm_prep    = "./supporting_data/ecm_prep.json"
    ecm_results = "./results/ecm_results.json"
    debug       = False
    port        = 8050

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_usage)
            print(help_options)
            sys.exit()
        elif opt in ("--ecm_results"):
            ecm_results = arg
        elif opt in ("--ecm_prep"):
            ecm_prep = arg
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-p", "--port"):
            port = arg

    if not os.path.exists(ecm_prep):
        print(f"{ecm_prep} can not be reached or does not exist.")
        sys.exit(1)
    if not os.path.exists(ecm_results):
        print(f"{ecm_results} can not be reached or does not exist.")
        sys.exit(1)

    ############################################################################
    # Import the Data sets
    #print(f"Importing data from {ecm_prep}")
    #ecm_prep = ECM_PREP(path = ecm_prep)

    print(f"Importing data from {ecm_results}")
    ecm_results = ECM_RESULTS(path = ecm_results)

    ############################################################################
    # build useful things for ui
    ecms = [{"label" : l, "value" : l} 
            for l in set(ecm_results.financial_metrics.ecm)]
    years = [y for y in set(ecm_results.mas_by_category.year)]
    years.sort()

    ############################################################################
    # run the dash app
    print("Launching dash app")
    app.run_server(port = port, debug = debug)



################################################################################
#                                 End of File                                  #
################################################################################

