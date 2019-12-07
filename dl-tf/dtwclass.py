#! C:/Python27/python

"""
    Compute a distance matrix on 2 multi-parameter vectors from 2 utterances
    and perform dynamic time warping on the distance matrix

        The final warp matrix plot the warping index from index x to index y in each frame
        For example
        
        [[   0.    0.   ]
         [   1.    1.   ] 
         [   2.    2.   ]  
         ..., 
         [ 645.  868.   ] 
         [ 646.  868.   ]  
         [ 647.  869.   ]  
    

    This program refers to
    
        /* dtw.c */
        /* VERSION 2.0 Andrew Slater, 20/8/1999 */
        /* Latest changes 3/2006 by John Coleman */
        
"""

import sys
import math
import numpy as np


class Dtw():
    class Dict(dict):
          def __getitem__(self, s):
                try:
                    return super(Dtw.Dict, self).__getitem__(s)
                except KeyError:
          	        return np.inf

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.xsize = len(x)
        self.ysize = len(y)
        self.vecsize = len(x[0])
        self.Dist = []  # Distance matrix
        self.globdist = [] # global distance 
        self.warp = [] # warped trajectory
        self.LARGEVALUE = (1e+30)
                
    def compute_dist(self):
        Dist = []
        x=self.x
        y=self.y

        for i in range(0,self.xsize):
            Dist_i = []
            for j in range(0,self.ysize):
                total = 0
                for k in range(0,self.vecsize):                    
                    total += (x[i][k] - y[j][k])*(x[i][k] - y[j][k])
                Dist_i += [total]
            Dist += [(Dist_i)]
        return Dist

    def CalcFrameBasedSpectrumWeight(self,reflsp,lsporder):
                
        refweight=[]
        for i in range(0, lsporder):
            weight=1
            if i==0:
                weight=1/reflsp[0]+1/math.fabs(reflsp[1] -reflsp[0])
            elif i==lsporder-1:
                weight=1/math.fabs(reflsp[i] - reflsp[i-1]) + 1/(0.5-reflsp[i])
            else:
                weight = 1/math.fabs(reflsp[i] - reflsp[i-1]) + 1/math.fabs(reflsp[i+1] - reflsp[i])
            refweight+=[weight]
        return refweight
        
    def compute_lsp_dist(self): 
        Dist = []
        x = self.x
        y = self.y

        for i in range (0,self.xsize):
            Dist_i = []
            for j in range(0, self.ysize):
                refweight=self.CalcFrameBasedSpectrumWeight(x[i],self.vecsize)
                total =0
                for k in range(0, self.vecsize-1):
                    total += (x[i][k] - y[j][k])*(x[i][k] - y[j][k])*refweight[k]
                    total +=  (x[i][k+1] - y[j][k+1])*(x[i][k+1] - y[j][k+1])
                Dist_i +=[total]
            Dist += [(Dist_i)]
        return Dist
        
    def warp_distance(self):
                
        warp = self.warp
        xsize = self.xsize
        ysize = self.ysize
        
        Dist = self.compute_lsp_dist()
        self.Dist = Dist
        
        globdist = np.zeros((xsize,ysize))
        move = np.zeros((xsize,ysize))
        temp = np.zeros((xsize+1,ysize+1))
    
        # for the first frame, only possible match is at [0][0]
        globdist [0][0] = Dist[0][0]
                
        for j in range(1,xsize):
            globdist[j][0] = self.LARGEVALUE
                
        # for the first moving          
        globdist[0][1] = self.LARGEVALUE
        globdist[1][1] = globdist[0][0] + Dist[1][1]
        move[1][1] = 2
                
        for j in range(2,xsize):
            globdist[j][1] = self.LARGEVALUE
                
        for i in range(2,ysize):
            globdist[0][i] = self.LARGEVALUE
            globdist[1][i] = globdist[0][i-1]+Dist[1][i]
                    
            for j in range(2,xsize):
                top = globdist[j-1][i-2] + Dist[j][i-1] + Dist[j][i]
                mid = globdist[j-1][i-1] + Dist[j][i]
                bot = globdist[j-2][i-1] + Dist[j-1][i] + Dist[j][i] 
                        
                if ( top < mid )and (top < bot):
                    cheapest = top
                    I=1
                elif ( mid < bot ):
                    cheapest = mid
                    I=2
                else:
                    cheapest = bot
                    I=3
                            
                if ( (top==mid) and (mid == bot)):
                    I=2
                        
                globdist[j][i]=cheapest
                move[j][i] = I
                        
        X=ysize-1
        Y=xsize-1
        n=0
        warp=np.zeros((xsize,2))
        warp[n][0]=X
        warp[n][1]=Y

        while( X>1 and Y>1):
            n+=1
            #print "Y="+str(Y)+" X="+str(X)+"move[Y][X]="+str(move[Y][X])
            if(n>ysize*2):
                print "Error: warp matrix too large!"
                sys.exit()
                
            if(move[Y][X] == 1):
                warp[n][0]=X-1
                warp[n][1]=Y
                n+=1
                X=X-2
                Y=Y-2
            elif(move[Y][X] == 2):
                X=X-1
                Y=Y-1
            elif(move[Y][X] == 3):
                warp[n][0]=X
                warp[n][1]=Y-1
                n+=1
                X=X-1
                Y=Y-2
            else:
                print "Error: move not defined for X="+str(X)+" Y="+str(Y)+" "
                sys.exit()
            
            warp[n][0]=X
            warp[n][1]=Y

    
        # flop warp
        for i in range(0, n+1):
            temp[i][0] = warp[n-i][0]
            temp[i][1] = warp[n-i][1]
            
        for i in range(0, n+1):
            warp[i][0] = temp[i][0]
            warp[i][1] = temp[i][1]
            #print str(warp[i][0])+"-"+str(warp[i][1])

        self.globdist = globdist
        self.warp = warp
        
        return self.warp        
                        
                
                
                
                
            
                
        
