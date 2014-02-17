import csv
import sys
import os.path
import string
import ROOT
ROOT.gROOT.SetBatch()

if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
    print "Required format: python MakeReviewPlots.py <delimited text file name>."
    sys.exit(1)

# Dialect (what delimiter is used).
# I recommend tab-delimited because some commas are used in the notes.
# 'excel-tab' for tab-delimited; 'excel' for comma-delimited.
delimiter_dialect = 'excel-tab'

Colors = {
    '136Xe' : ROOT.kRed,
    '76Ge' : ROOT.kBlue,
    '150Nd' : ROOT.kOrange,
    '130Te' : ROOT.kBlack,
    '100Mo' : ROOT.kGreen,
    '82Se' : ROOT.kCyan,
    '96Zr' : ROOT.kPink,
    '48Ca' : ROOT.kYellow,
}
MonthToYear = {
    'Jan' : 0./12,
    'Feb' : 1./12,
    'Mar' : 2./12,
    'Apr' : 3./12,
    'May' : 4./12,
    'Jun' : 5./12,
    'Jul' : 6./12,
    'Aug' : 7./12,
    'Sep' : 8./12,
    'Oct' : 9./12,
    'Nov' : 10./12,
    'Dec' : 11./12,
    ''    : 0./12, # Unfilled months are treated like January
}

# Hard-code the various plots we make.
# Each is a dictionary where keys are the desired isotopes; we need to initialize them
# to contain the desired isotopes (since generally we may not want to show all isotopes together).
halflife_vs_year = { # dict from isotope to a list of year-T1/2 pairs.
    '136Xe' : [], '136Xe_still_running' : [],
    '76Ge' : [], '76Ge_still_running' : [],
    '130Te' : [], '130Te_still_running' : [],
}
exposure_vs_year = { # dict from isotope to a list of year-exposure pairs.
    '136Xe' : [], '136Xe_still_running' : [],
    '76Ge' : [], '76Ge_still_running' : [],
    '130Te' : [], '130Te_still_running' : [],
}
halflife_vs_exposure = { # dict from isotope to a list of exposure-T1/2 pairs.
    '136Xe' : [], '136Xe_still_running' : [],
    '76Ge' : [], '76Ge_still_running' : [],
    '130Te' : [], '130Te_still_running' : [],
}

ListOfIsotopes = {} # Make a list of the best limits for every isotope.

with open(sys.argv[1], 'rb') as csvfile:
    reader = csv.DictReader(csvfile, dialect = delimiter_dialect)
    for row in reader:
        try:
            PublicationTime = float(row['year']) + MonthToYear[row['month']]
            isotope = row['Isotope']
            if row['Still running?'] == 'Y':
                isotope += '_still_running'

            # halflife_vs_year
            if (row['Isotope'] in halflife_vs_year and
                row['T_{1/2} limit (yrs)'] != ''):
                halflife_vs_year[isotope].append((PublicationTime,
                                                  float(row['T_{1/2} limit (yrs)'])))

            # exposure_vs_year
            if (row['Isotope'] in exposure_vs_year and
                row['Exposure (mol-yrs)'] != ''):
                exposure_vs_year[isotope].append((PublicationTime,
                                                  float(row['Exposure (mol-yrs)'])))

            # halflife_vs_exposure
            if (row['Isotope'] in halflife_vs_exposure and
                row['T_{1/2} limit (yrs)'] != '' and
                row['Exposure (mol-yrs)'] != ''):
                halflife_vs_exposure[isotope].append((float(row['Exposure (mol-yrs)']),
                                                      float(row['T_{1/2} limit (yrs)'])))

            # Accumulate list of top limits
            if (row['Isotope'] not in ListOfIsotopes or
                ListOfIsotopes[row['Isotope']][0] < float(row['T_{1/2} limit (yrs)'])):
                ListOfIsotopes[row['Isotope']] = (float(row['T_{1/2} limit (yrs)']),
                                                  row['Collaboration'],
                                                  row['year'],
                                                  row['C.L. (%)'])

        except ValueError:
            print "Could not convert values in one row; skipping."

c = ROOT.TCanvas()

# Make "white" be transparent (only works for pdf, svg, a few others but not eps).
ROOT.gROOT.GetColor(ROOT.kWhite).SetAlpha(0)

# No plot titles.
ROOT.gStyle.SetOptTitle(0)

# Transform the isotope into a pretty Latex format.
# I assume that the isotope input is in a form like 136Xe.
def PrettyIsotope(isotope):
    firstletter = 0
    while firstletter < len(isotope) and isotope[firstletter] not in string.ascii_letters:
        firstletter += 1
    return '^{' + isotope[:firstletter] + '}' + isotope[firstletter:]

# Define one style of plot -- a scatter plot of yvar vs xvar,
# color-coded for the different isotopes.
# So, datapoints is a map from isotope to a list of xy-points.
def DrawGraph(xvarlabel, yvarlabel, datapoints, legend_pos, image_name,
              xaxisrange = None, yaxisrange = None, xtype = 'Lin', ytype = 'Log'):
    if xtype == 'Log': c.SetLogx()
    if ytype == 'Log': c.SetLogy()
    c.SetGridy()
    dict_of_graphs = {}
    legend = ROOT.TLegend(*legend_pos)
    for isotope in datapoints:
        isotope_name = isotope
        still_running = False
        if len(isotope) >= 14 and isotope[-14:] == '_still_running':
            still_running = True
            isotope_name = isotope[:-14]
        gr_size = len(datapoints[isotope])
        if gr_size == 0: continue
        gr = ROOT.TGraph(gr_size)
        for point in range(gr_size):
            gr.SetPoint(point, datapoints[isotope][point][0], datapoints[isotope][point][1])
        if still_running: gr.SetMarkerStyle(ROOT.kOpenCircle)
        else: gr.SetMarkerStyle(ROOT.kFullCircle)
        gr.SetMarkerColor(Colors[isotope_name])
        gr.SetLineColor(ROOT.kWhite)
        gr.SetFillColor(ROOT.kWhite)
        dict_of_graphs[isotope] = gr
        if not still_running: legend.AddEntry(dict_of_graphs[isotope], PrettyIsotope(isotope_name))
    multigraph = ROOT.TMultiGraph()
    for gr in dict_of_graphs.itervalues(): multigraph.Add(gr, "p")
    multigraph.Draw("a")
    multigraph.GetXaxis().SetTitle(xvarlabel)
    multigraph.GetYaxis().SetTitle(yvarlabel)
    multigraph.GetXaxis().SetTitleSize(0.04)
    multigraph.GetYaxis().SetTitleSize(0.04)
    multigraph.GetXaxis().CenterTitle()
    multigraph.GetYaxis().CenterTitle()
    multigraph.GetXaxis().SetTitleOffset(1.1)
    multigraph.GetYaxis().SetTitleOffset(1.1)
    multigraph.GetXaxis().SetTitleFont(12)
    multigraph.GetYaxis().SetTitleFont(12)
    if xaxisrange != None: multigraph.GetXaxis().SetLimits(*xaxisrange)
    if yaxisrange != None: multigraph.GetYaxis().SetRangeUser(*yaxisrange)
    legend.SetFillColor(ROOT.kWhite)
    legend.SetBorderSize(0)
    legend.SetTextFont(12)
    legend.Draw()
    c.SaveAs(image_name)

DrawGraph("Publication Year",
          "T_{1/2} Limit (years)",
          halflife_vs_year,
          (0.2, 0.6, 0.4, 0.8),
          "halflife_vs_year.pdf",
          yaxisrange = (1.e20, 4.e26))

DrawGraph("Publication Year",
          "Exposure (mol-years)",
          exposure_vs_year,
          (0.7, 0.2, 0.9, 0.4),
          "exposure_vs_year.pdf",
          yaxisrange = (1.e-1, 4.e3))

DrawGraph("Exposure (mol-years)",
          "T_{1/2} Limit (years)",
          halflife_vs_exposure,
          (0.2, 0.6, 0.4, 0.8),
          "halflife_vs_exposure.pdf",
          xaxisrange = (3e-1, 1e3),
          yaxisrange = (1e22, 1e26),
          xtype = 'Log')

print "The best limits obtained are:"
for key in ListOfIsotopes:
    print "%s: %.1e, %s %s (CL %s)" % (key,
                                       ListOfIsotopes[key][0],
                                       ListOfIsotopes[key][1],
                                       ListOfIsotopes[key][2],
                                       ListOfIsotopes[key][3])
