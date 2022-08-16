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
from plots_utilities import ECM_PREP_VS_RESULTS

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
            html.Label("Select Type of Graphic:"),
            dcc.Dropdown(id = "fm_dropdown",
                options = [
                    {"label" : "Aggregated overall All ECMs", "value" : "agg_ecms"},
                    {"label" : "Plot all ECMs in one graphic", "value" : "all_ecms"},
                    {"label" : "Plot a Selected ECM:", "value" : "each_ecm"}
                    ],
                value = "agg_ecms",
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
            style = {"min-width" : "500px", "display" : "none"}
            ),
        html.Hr(),
        dcc.Loading(
            id = "loading-fm-output-container",
            children = html.Div(
                    id = "fm-output-container",
                    style = {
                        'border': '1px solid black',
                        'width' : '1200px',
                        'height': '900px'
                        }
                    ),
            type = "default")
            ]
        )
    return pg

@app.callback(
        Output(component_id = 'ecm_dropdown_div', component_property = "style"),
        Input(component_id = 'fm_dropdown', component_property = 'value')
        )
def show_hide_ecm_dropdown(value):
    if value == "each_ecm":
        return {"width" : "25%", "display" : "inline-block"}
    else:
        return {"width" : "25%", "display" : "none"}

@app.callback(
        Output('fm-output-container', 'children'),
        Input('fm_dropdown', 'value'),
        Input('ecm_dropdown', 'value')
        )
def update_fm_output(fm_dropdown_value, ecm_dropdown_value):
    if fm_dropdown_value == "agg_ecms":
        return dcc.Graph(figure = ecm_results.generate_fm_agg_ecms())
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
                    {"label" : i, "value" : i} for i in impact_dict.values()
                    ],
                value = list(impact_dict.values())[0],
                clearable = False
                )],
            style = {"width" : "300px", "display" : "inline-block"}
            ),
        html.Div([
            html.Label("Year:"),
            dcc.Dropdown(id = "year_dropdown",
                options = years,
                value = years[0],
                clearable = False)],
            id = "year_dropdown_div",
            style = {"min-width" : "125px", "display" : "inline-block"}),
        html.Br(),
        html.Div([
            html.Label("Included End Uses:"),
            dcc.Dropdown(id = "end_uses_dropdown",
                options = [{"label" : l, "value" : l} for l in end_uses],
                value = end_uses,
                multi = True,
                clearable = False
                )],
            id = "end_uses_dropdown_div",
            style = {"min-width" : "500px", "display" : "inline-block"}),
        html.Br(),
        html.Div([
            html.Label("Included Building Classes:"),
            dcc.Dropdown(id = "building_classes_dropdown",
                options = [{"label" : l, "value" : l} for l in building_classes],
                value = building_classes,
                multi = True,
                clearable = False
                )],
            id = "building_classes_dropdown_div",
            style = {
                "min-width" : "500px",
                **({"display" : "none"} if building_classes[0] is None else {"display" : "inline-block"})
                }
            ),
        html.Br(),
        html.Div([
            html.Label("Included Building Types:"),
            dcc.Dropdown(id = "building_types_dropdown",
                options = [{"label" : l, "value" : l} for l in building_types],
                value = building_types,
                multi = True,
                clearable = False
                )],
            id = "building_types_dropdown_div",
            style = {
                "min-width" : "500px",
                **({"display" : "none"} if building_types[0] is None else {"display" : "inline-block"})
                }
            ),
        html.Hr(),
        dcc.Loading(
            id = "loading-cse-output-container",
            children = html.Div(
                id = "ces-output-container",
                style = {
                    'border': '1px solid black',
                    'width' : '1200px',
                    'height': '900px'
                    }
                ),
            type = "default"
            )
    ])
    return pg

@app.callback(
        Output('ces-output-container', 'children'),
        Input('ces_cce_dropdown', 'value'),
        Input('year_dropdown', 'value'),
        Input('end_uses_dropdown', 'value'),
        Input('building_classes_dropdown', 'value'),
        Input('building_types_dropdown', 'value')
        )
def update_ces_output(ces_dropdown_value,
        year_dropdown_value,
        end_uses_dropdown_value,
        building_classes_dropdown_value,
        building_types_dropdown_value
        ):
    return dcc.Graph(figure =
            ecm_results.generate_cost_effective_savings(
                m = ces_dropdown_value,
                year = year_dropdown_value,
                end_uses = end_uses_dropdown_value,
                building_classes = building_classes_dropdown_value,
                building_types = building_types_dropdown_value
            )
        )

def total_savings():
    savings_by_dropdown_options = [
            {"label" : "Overall",           "value" : "overall"},
            {"label" : "By Region ",        "value" : "region"},
            {"label" : "By End Use",        "value" : "end_use"},
            ]
    if building_classes[0] is not None:
        savings_by_dropdown_options.append(
            {"label" : "By Building Class", "value" : "building_class"}
            )
    if building_types[0] is not None:
        savings_by_dropdown_options.append(
            {"label" : "By Building Type",  "value" : "building_type"},
            )

    pg = html.Div([
        html.H1("Total Savings"),
        html.Div([
            html.Label("Impact:"),
            dcc.Dropdown(id = "savings_dropdown",
                options = [
                    {"label" : i, "value" : i} for i in impact_dict.values()
                    ],
                value = list(impact_dict.values())[0],
                clearable = False
                )],
            style = {"width" : "25%", "display" : "inline-block"}
            ),
        html.Div([
            html.Label("Aggregate by:"),
            dcc.Dropdown(id = "savings_by_dropdown",
            options = savings_by_dropdown_options,
            value = "overall",
            clearable = False
            )],
            id = "savings_by_dropdown_div",
            style = {"min-width" : "400px", "display" : "inline-block"}
            ),
        html.Div([
            html.Label("Annual or Cumulative Totals?"),
            dcc.Dropdown(id = "savings_annual_cumulative_dropdown",
            options = [
                {"label" : "Annual Totals",     "value" : "annual"},
                {"label" : "Cumulative Totals", "value" : "cumulative"}
                ],
            value = "annual",
            clearable = False
            )],
            id = "savings_annual_cumulative_dropdown_div",
            style = {"min-width" : "400px", "display" : "inline-block"}
            ),
        html.Hr(),
        dcc.Loading(
            id = "loading-savings-output-container",
            children = html.Div(
                id = "savings-output-container",
                style = {
                    'border': '1px solid black',
                    'width' : '1200px',
                    'height': '900px'
                    }),
            type = "default"
            )
        ])
    return pg

@app.callback(
        Output("savings-output-container", 'children'),
        Input("savings_dropdown", "value"),
        Input("savings_by_dropdown", "value"),
        Input("savings_annual_cumulative_dropdown", "value")
        )
def update_savings_output(savings_dropdown_value, savings_by_dropdown_value, savings_annual_cumulative_dropdown):

    if savings_by_dropdown_value == "overall":
        savings_by_dropdown_value = None

    return dcc.Graph(figure = ecm_results.generate_total_savings(
        m = savings_dropdown_value,
        by = savings_by_dropdown_value,
        annual_or_cumulative = savings_annual_cumulative_dropdown
        ))

def cms_v_ums():
    pg = html.Div([
        html.H1("Competed versus Uncompeted"),
        html.Div([
            html.Label("Select Type of Graphic:"),
            dcc.Dropdown(id = "cms_v_ums_type_dropdown",
                options = [
                    {"label" : "Plot a Selected ECM:", "value" : "each_ecm"}
                    ],
                value = "each_ecm",
                clearable = False
                )],
            style = {"width" : "25%", "display" : "inline-block"}
            ),
        html.Div([
            html.Label("ECM:"),
            dcc.Dropdown(id = "cms_v_ums_ecm_dropdown",
                options = ecms,
                value = ecms[0]["value"],
                clearable = False)
            ],
            id = "cms_v_ums_ecm_dropdown_div",
            style = {"min-width" : "500px", "display" : "none"}
            ),
        html.Hr(),
        dcc.Loading(
            id = "loading-cms_v_ums-output-container",
            children = html.Div(
                    id = "cms_v_ums-output-container",
                    style = {
                        'border': '1px solid black',
                        'width' : '1200px',
                        'height': '900px'
                        }
                    ),
            type = "default")
        ])
    return pg

@app.callback(
        Output(component_id = 'cms_v_ums_ecm_dropdown_div', component_property = "style"),
        Input(component_id = 'cms_v_ums_type_dropdown', component_property = 'value')
        )
def show_hide_cms_v_ums_ecm_dropdown(value):
    if value == "each_ecm":
        return {"width" : "25%", "display" : "inline-block"}
    else:
        return {"width" : "25%", "display" : "none"}


@app.callback(
        Output("cms_v_ums-output-container", "children"),
        Input("cms_v_ums_type_dropdown", "value"),
        Input("cms_v_ums_ecm_dropdown", "value")
        )
def update_cms_v_ums_output(
        cms_v_ums_type_dropdown_value,
        cms_v_ums_ecm_dropdown_value
        ):

    if (cms_v_ums_type_dropdown_value == "each_ecm"):
        fig = ecm_prep_v_results.generate_by_ecm(cms_v_ums_ecm_dropdown_value)

    return dcc.Graph(figure = fig)


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
    ecm_prep_path    = "./supporting_data/ecm_prep.json"
    ecm_results_path = "./results/ecm_results.json"
    debug            = False
    port             = 8050

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_usage)
            print(help_options)
            sys.exit()
        elif opt in ("--ecm_results"):
            ecm_results_path = arg
        elif opt in ("--ecm_prep"):
            ecm_prep_path = arg
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-p", "--port"):
            port = arg

    if not os.path.exists(ecm_prep_path):
        print(f"{ecm_prep_path} can not be reached or does not exist.")
        sys.exit(1)
    if not os.path.exists(ecm_results_path):
        print(f"{ecm_results_path} can not be reached or does not exist.")
        sys.exit(1)

    ############################################################################
    # Import the Data sets
    print(f"Importing data from {ecm_prep_path}")
    ecm_prep = ECM_PREP(path = ecm_prep_path)

    print(f"Importing data from {ecm_results_path}")
    ecm_results = ECM_RESULTS(path = ecm_results_path)

    print(f"Building data set for Unompeted versus Competed metrics")
    ecm_prep_v_results = ECM_PREP_VS_RESULTS(ecm_prep, ecm_results)

    ############################################################################
    # build useful things for ui
    ecms = list(set(ecm_results.financial_metrics.ecm))
    ecms.sort()
    ecms = [{"label" : l, "value" : l} for l in ecms]

    years = [y for y in set(ecm_results.mas_by_category.year)]
    years.sort()

    impacts = [i for i in set(ecm_results.mas_by_category.impact)]
    
    impact_dict = {"carbon" : "", "cost" : "", "energy" : ""}
    m = [x for x in impacts if x.startswith("Avoided CO\u2082 Emissions")]
    assert len(m) == 1
    impact_dict["carbon"] = m[0]

    m = [x for x in impacts if x.startswith("Energy Cost Savings")]
    assert len(m) == 1
    impact_dict["cost"] = m[0]

    m = [x for x in impacts if x.startswith("Energy Savings")]
    assert len(m) == 1
    impact_dict["energy"] = m[0]

    end_uses = list(set(ecm_results.mas_by_category.end_use))
    end_uses.sort()

    # because building_class and building_type may or may not be in the results,
    # yeah, that's a thing, you'll need to build this project to address the
    # cases with and with out.
    if "building_class" in ecm_results.mas_by_category.columns:
        building_classes = list(set(ecm_results.mas_by_category.building_class))
        building_classes.sort()
    else:
        building_classes = [None]

    if "building_type" in ecm_results.mas_by_category.columns:
        building_types = list(set(ecm_results.mas_by_category.building_type))
        building_types.sort()
    else:
        building_types = [None]


    ############################################################################
    # run the dash app
    print("Launching dash app")
    app.run_server(port = port, debug = debug)



################################################################################
#                                 End of File                                  #
################################################################################

