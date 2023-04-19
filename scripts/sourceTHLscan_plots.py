from ROOT import TFile, TH1F, TH2F
import sys

#Code for threshold calibration:
#This code is used to analyse data from a threshold scan for an Xray exposure onto a CLICpix2 device
#Reads in a data file from each matrix configuration and storeds the data
#Does a simple clustering algorithm to only use single pixel clusters
#Creates different profiles and histograms wrt ToT and counts

outputfile = TFile("sourceTHLscan_plots.root", "recreate")

h_count=TH1F("h_count", "h_count", 2299, 0,2299)
h_count_even=TH1F("h_count_even", "h_count_even", 2299, 0,2299)
h_count_odd=TH1F("h_count_odd", "h_count_odd", 2299, 0,2299)

h_diffcount=TH1F("h_diffcount", "h_diffcount", 2299, 0,2299)
h_ToT=TH1F("h_ToT", "h_ToT", 30, 0,30)

thl=1284
hitmap=TH2F("hitmap","hitmap;x;y",128,0,128,128,0,128)
end_thl=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

num_files=len(sys.argv)-1
filenum=0
n=0
numpix=128

for filename in sys.argv:
    if (n==0):
        n=n+1
        continue
    linenum=-1
    previousthl=10000
    first_frame=True
    Matrix_counts=[[0 for x in range(numpix)] for y in range(numpix)]
    Matrix_tot=[[0 for x in range(numpix)] for y in range(numpix)]
    file=open(filename, "r")
    print("Opened file " + filename)
    for line in file:
        linenum=linenum+1
        # line structure: threshold,pix col, pix row, hit flag, tot, count
        # actual line structure: threshold,pix col, pix row, hit flag, count
        l=line.split(",")
        # PG: original line: if l[0].isdigit()==False or len(l)<6:
        if l[0].isdigit()==False or len(l)<5:
            continue
        l_2=l[-1].split("\n")
        if l_2[0].isdigit()!=True:
            continue
        counts=int(l_2[0])
        ToT=int(l[4])
        ToT=0
        if counts==0:
            continue
        hitmap.Fill(int(l[1]),int(l[2]),counts)
        THLdac=int(l[0])
        if THLdac<end_thl[filenum]:
            print("breaking file" + filename + "at threshold" + THLdac)
            break

        if first_frame==True:
            previousthl=THLdac
            first_frame=False
        elif(THLdac<previousthl):
            # new thl, calculating single pixel clusters and resetting the hit map
            ##loop to add info to histos
            for i in range(0,numpix):
                for j in range(0,numpix):
                    if (Matrix_counts[i][j]==0):
                        continue
                    single=True
                    # print "Next hit pixel under consideration: [",i,",",j,"]"
                    #looking for neighbours of pixel i,j
                    for ii in range(i-1,i+2):
                        for jj in range(j-1,j+2):
                            # print "    Looking at neighbour [",ii,",",jj,"]"
                            if (ii==i and jj==j):
                                # print "        skipping central pixel..."
                                #skip central pixel ij
                                continue
                            if (ii<0 or jj<0 or ii>=numpix or jj>=numpix):
                                # print "        skipping pixel outside matrix..."
                                #skip neighbour if outside pixel matrix range
                                continue
                            if(Matrix_counts[ii][jj]!=0):
                                # print "    Neighbour [",ii,",",jj,"] has counts of ",Matrix_counts[ii][jj]," so considered pixel is not single"
                                single=False
                                # single =True
                    if (single==True):
                        # print "    Considered pixel is single! Adding to histos"
                        h_count.Fill(previousthl,Matrix_counts[i][j])
                        if(i%2==0):
                            h_count_even.Fill(previousthl,Matrix_counts[i][j])
                        else:
                            h_count_odd.Fill(previousthl,Matrix_counts[i][j])
            #print "Waiting..."
            #raw_input()

            Matrix_counts=[[0 for x in range(numpix)] for y in range(numpix)]
            Matrix_tot=[[0 for x in range(numpix)] for y in range(numpix)]
            previousthl=THLdac

        Matrix_counts[int(l[1])][int(l[2])]=counts
        Matrix_tot[int(l[1])][int(l[2])]=ToT

    #single pixel testing for final frame
    for i in range(0,numpix):
        for j in range(0,numpix):
            single=True
            #looking for neighbours of pixel i,j
            for ii in range(i-1,i+1):
                for jj in range(j-1,j+1):
                    if (ii==i and jj==j):
                        #skip central pixel ij
                        continue
                    if (ii<0 or jj<0 or ii>numpix or jj>numpix):
                        #skip neighbour if outside pixel matrix range
                        continue
                    if(Matrix_counts[ii][jj]!=0):
                        single=False
                        # single=True
            if (single==True):
                h_count.Fill(THLdac,Matrix_counts[i][j])
                if(i%2==0):
                    h_count_even.Fill(previousthl,Matrix_counts[i][j])
                else:
                    h_count_odd.Fill(previousthl,Matrix_counts[i][j])


    filenum=filenum+1
    file.close()
    n=n+1

max_entries=0
max_entries_odd=0
max_entries_even=0

for i in range(0,2999):
    if (h_count.GetBinContent(i)>max_entries):
        max_entries=h_count.GetBinContent(i)
    if (h_count_even.GetBinContent(i)>max_entries_even):
        max_entries_even=h_count_even.GetBinContent(i)
    if (h_count_odd.GetBinContent(i)>max_entries_odd):
        max_entries_odd=h_count_odd.GetBinContent(i)

    difference=h_count.GetBinContent(i) - h_count.GetBinContent(i+1)
    h_diffcount.Fill(i,difference)

if max_entries > 0:
    h_count.Scale(1/max_entries)
if max_entries_even:
    h_count_even.Scale(1/max_entries_even)
if max_entries_odd > 0:
    h_count_odd.Scale(1/max_entries_odd)

outputfile.cd()
dir = outputfile.mkdir("Directory")
dir.cd()
dir.WriteObject(hitmap,"Hitmap", "hist")
dir.WriteObject(h_count,"Hist: Counts vs. THLdac", "hist")
dir.WriteObject(h_count_even,"Hist: Counts vs. THLdac (even)", "hist")
dir.WriteObject(h_count_odd,"Hist: Counts vs. THLdac (odd)", "hist")
dir.WriteObject(h_ToT,"Hist: ToT for particular THL", "hist")
dir.WriteObject(h_diffcount,"Hist: difference in Counts vs. THLdac", "hist")
outputfile.Close()
