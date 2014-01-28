import csv
import sys
import os.path
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

# Hard-code the various plots we make.
# Each is a dictionary where keys are the desired isotopes; we need to initialize them
# to contain the desired isotopes (since generally we may not want to show all isotopes together).
halflife_vs_year = { # dict from isotope to a list of T1/2-year pairs.
    '136Xe' : [],
    '76Ge' : [],
    '130Te' : [],
}
exposure_vs_year = { # dict from isotope to a list of exposure-year pairs.
    '136Xe' : [],
    '76Ge' : [],
    '130Te' : [],
}

with open(sys.argv[1], 'rb') as csvfile:
    reader = csv.DictReader(csvfile, dialect = delimiter_dialect)
    for row in reader:

        # halflife_vs_year
        if (row['Isotope'] in halflife_vs_year and
            row['T_{1/2} limit (yrs)'] != '' and
            row['year'] != ''):
            halflife_vs_year[row['Isotope']].append((float(row['year']),
                                                     float(row['T_{1/2} limit (yrs)'])))

        # exposure_vs_year
        if (row['Isotope'] in exposure_vs_year and
            row['Exposure (mol-yrs)'] != '' and
            row['year'] != ''):
            exposure_vs_year[row['Isotope']].append((float(row['year']),
                                                     float(row['Exposure (mol-yrs)'])))

c = ROOT.TCanvas()

# Define one style of plot -- a scatter plot of yvar vs xvar,
# color-coded for the different isotopes.
# So, datapoints is a map from isotope to a list of xy-points.
def DrawGraph(title, xvarlabel, yvarlabel, datapoints, legend_pos, image_name):
    c.SetLogy()
    c.SetGridy()
    dict_of_graphs = {}
    for isotope in datapoints:
        gr_size = len(datapoints[isotope])
        gr = ROOT.TGraph(gr_size)
        for point in range(gr_size):
            gr.SetPoint(point, datapoints[isotope][point][0], datapoints[isotope][point][1])
        gr.SetMarkerColor(Colors[isotope])
        gr.SetLineColor(Colors[isotope])
        gr.SetFillColor(Colors[isotope])
        dict_of_graphs[isotope] = gr
    multigraph = ROOT.TMultiGraph()
    for gr in dict_of_graphs.itervalues(): multigraph.Add(gr, "p*")
    multigraph.SetTitle(title)
    multigraph.Draw("a")
    multigraph.GetXaxis().SetTitle(xvarlabel)
    multigraph.GetYaxis().SetTitle(yvarlabel)
    legend = ROOT.TLegend(*legend_pos)
    for isotope in dict_of_graphs: legend.AddEntry(dict_of_graphs[isotope], isotope)
    legend.Draw()
    c.SaveAs(image_name)

DrawGraph("Halflife vs Publication Year",
          "Publication Year",
          "T_{1/2} Limit (years)",
          halflife_vs_year,
          (0.1, 0.7, 0.3, 0.9),
          "halflife_vs_year.eps")

DrawGraph("Exposure vs Publication Year",
          "Publication Year",
          "Exposure (mol-years)",
          exposure_vs_year,
          (0.7, 0.1, 0.9, 0.3),
          "exposure_vs_year.eps")
