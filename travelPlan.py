import sys
import csv
import random
import copy

def convertTime(time):
        hour = int(time)
        minute = int((time-hour)*60)
        if minute < 10:
            minute = "0"+str(minute)
        return str(hour)+":"+str(minute)

class Destination:
    def __init__(self, name, description=None, category=None, address=None, cost=None, openHour=None, closeHour=None, closedDays=None, duration=None, fun=None):
        self.name = name
        self.description = description
        self.category = category
        self.address = address
        self.cost = cost
        self.openHour = openHour
        self.closeHour = closeHour
        self.closedDays = closedDays
        self.duration = duration
        self.fun = fun

        self.priorityScore = 0


    
    def __repr__(self):
        s = "Destination: " + self.name + "\n" + "Address: " + self.address + "\n" 
        s += "Cost: " + str(self.cost) + "\n" + "Duration: "+ str(self.duration)+ "\n" 
        s += "Open Hours: " + convertTime(self.openHour) + "-" + convertTime(self.closeHour) + "\n"
        s += "Fun: "+ str(self.fun)+"/10\n"
        #s += "Closed on: " + str(self.closedDays) + "\n"
        #return s
        return self.name+"\n"

class TravelPlanner:
    def __init__(self, startDay, lengthOfTravel, startTime, endTime, budgetLimit, interests, startDest, destCSV, distCSV, timeCSV):

        # user specified
        self.hotel = Destination("Double Tree Hotel")
        self.startDay = startDay
        self.lengthOfTravel = lengthOfTravel
        self.startTime = startTime
        self.endTime = endTime
        self.budgetLimit = budgetLimit
        self.interests = interests
        #["Outdoor and Adventure", "Event and Amusement", "Culture and Landmarks"]

        self.destinations = self.getDestinations(destCSV)
        self.travelMatrix = self.getTravelMatrix(timeCSV, distCSV)

        self.currentTime = startTime
        self.currentDay = startDay
        self.moneySpent = 0
        self.daysTraveled = 0
        self.currentDest = self.hotel

        self.itinerary = []
        self.destTraveled = 0
        self.funHad = 0


    def getTravelMatrix(self, timeCSV, distCSV):
        time=list(csv.reader(open(timeCSV,'rb'),delimiter=','))
        distance=list(csv.reader(open(distCSV,'rb'),delimiter=','))
        matrix = dict()

        for i in range(1,20):
            for j in range(1,20):
                time[i][j]=float(time[i][j])
                distance[i][j]=float(distance[i][j])

        travelMatrix=dict()
        locations = time[0][1:]

        for i in range(len(locations)): 
            startingPoint = time[i+1][0]
            for j in range(len(locations)):
                destination = time[0][j+1]
                travelMatrix[(startingPoint,destination)] = (time[i+1][j+1],distance[i+1][j+1])

        return travelMatrix

    def getTravelTime(self, destA, destB):
        return float(self.travelMatrix[(destA.name,destB.name)][0])


    def getDestinations(self, destCSV):
        stonereader =csv.reader(open(destCSV,'rb'),delimiter=',')
        siyaoreader = csv.reader(open(destCSV, 'rU'), delimiter=',')
        data=list(siyaoreader)
        for i in range(1,len(data)):
            data[i][4]=float(data[i][4])
            data[i][5]=float(data[i][5])
            data[i][6]=float(data[i][6])
            data[i][8]=float(data[i][8])
            data[i][9]=float(data[i][9])
            data[i][7]=data[i][7].split(",")
        return data

    def constraint(self,dest):
        #print "checking ", dest.name, "on Day", self.daysTraveled+1, " at ", convertTime(self.currentTime)
        travelTime = self.getTravelTime(self.currentDest, dest)
        timeToHotel = self.getTravelTime(dest, self.hotel)
        maxWaitTime = 0.5
        if self.currentTime+travelTime + maxWaitTime < dest.openHour:
            #print "not open"
            return False
        if self.currentTime+travelTime + dest.duration > dest.closeHour:
            #print "closed" 
            return False
        if self.currentDay in dest.closedDays: 
            #print "closed on ", self.currentDay
            return False
        if self.moneySpent+dest.cost > self.budgetLimit:
            #print "exceed budget" 
            return False
        if dest.category not in self.interests:
            #print "not interested" 
            return False
        if self.daysTraveled > self.lengthOfTravel:
            #print "exceed lengthOfTravel"
            return False
        if self.currentTime+travelTime+dest.duration > self.endTime:
            #print "too late"
            return False

        #print "passed constraint check"
        return True

    def getPriorityScore(self, dest, costWeight = 5, funWeight = 5, timeWeight = 5, durationWeight = 10):
        #print dest.name
        score = 47
        # budget
        score -= dest.cost/self.budgetLimit * costWeight
        costScore = (dest.cost/(self.budgetLimit-self.moneySpent)) *costWeight
        score-=costScore
        # fun
        funScore = (dest.fun/10) * funWeight
        score += funScore
        # time
        travelTime = self.getTravelTime(self.currentDest, dest)
        travelScore = travelTime*timeWeight
        score -= travelScore

        timeWasted = max(0, dest.openHour-self.currentTime-travelTime)
        travelToDurationScore = ((travelTime+timeWasted)/dest.duration) * timeWeight *0.5
        score -= travelToDurationScore

        timeLeft = self.endTime-self.currentTime
        if timeLeft <= 0:
            travelToTimeLeftScore = timeWeight
        else:
            travelToTimeLeftScore = ((travelTime+timeWasted)/timeLeft) * timeWeight *0.5
        score -= travelToTimeLeftScore

        # duration
        actualDuration = min(dest.closeHour - (self.currentTime+travelTime),dest.duration)
        durationScore = (actualDuration/dest.duration) * durationWeight
        score += durationScore
        
        # special cases:
        if travelTime < 0.1:
            # in the same neighborhood, should go
            score +=10

        #distance from hotel
        if self.currentTime > 16 and timeLeft  > 0:
            timeToHotel = self.getTravelTime(dest, self.hotel)
            score -= (timeToHotel/timeLeft)*10

        #print score, costScore, funScore, travelScore,travelToDurationScore, travelToTimeLeftScore,durationScore
        return score

    def incrementTime(self):
        self.currentTime+=1
        if (self.currentTime>=24):
            self.incrementDay()


    def incrementDay(self):
        daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(len(daysOfWeek)):
            if (self.currentDay == daysOfWeek[i]):
                self.currentDay = daysOfWeek[(i+1)%7]
                self.currentTime = self.startTime
                self.daysTraveled +=1
                self.currentDest = self.hotel
                return

    def addToItinerary(self,assignment):
        self.itinerary.append(assignment)
        if type(assignment) == Assignment:
            self.destTraveled +=1
            self.funHad +=assignment.dest.fun



class Assignment(object):
    def __init__(self, currentDay, currentTime, currentMoney, dest=None, travelTime=0, mealbreak=False):
        self.dest = dest
        self.currentDay = currentDay
        self.currentTime = currentTime
        self.currentMoney = currentMoney
        self.travelTime = travelTime
        if (mealbreak):
            self.mealbreak = 1.5
        else:
            self.mealbreak = 0

    def __repr__(self):
        s = "Travel Time: "+ convertTime(self.travelTime) + "\n"
        s += self.currentDay + " "+ convertTime(self.currentTime) #+ " Spent: "+ str(self.currentMoney) + "\n"
        s += "\n" + str(self.dest)
        if self.mealbreak > 0:
            s+= "Take a " + str(self.mealbreak)+ " hour break, and have a delicious meal nearby! \n"
        #return s
        return self.dest.name
        

class Problem:
    def __init__(self, planner):
        self.planner = planner
        self.numDest = 0
        self.variables = []
        self.constraints = []

    def compPriority(self,destx,desty):
        xP = int(self.planner.getPriorityScore(destx)*10)
        yP = int(self.planner.getPriorityScore(desty)*10)
        return yP - xP

    def addVariable(self,variable):
        self.variables.append(variable)
        self.numDest +=1

    def addConstraint(self,constraint):
        self.constraints.append(constraint)

    def isComplete(self):
        if (self.planner.moneySpent >= self.planner.budgetLimit):
            return True
        if (self.planner.daysTraveled >= self.planner.lengthOfTravel):
            return True
        if (len(self.variables)==0):
            return True
        else:
            return False

    def addAssignment(self,assignment):
        self.planner.addToItinerary(assignment)

    def satisfyConstraints(self, variable):
        for constraint in self.constraints:
            if (not constraint(variable)):
                return False

        return True

    def incrementTime(self):
        self.planner.currentTime+=1
        if (self.planner.currentTime>=24):
            self.incrementDay()


    def incrementDay(self):
        daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(len(daysOfWeek)):
            if (self.planner.currentDay == daysOfWeek[i]):
                self.planner.currentDay = daysOfWeek[(i+1)%7]
                self.planner.currentTime = self.planner.startTime
                #print "incrementing day ", self.daysTraveled
                self.planner.daysTraveled +=1
                self.planner.currentDest = self.planner.hotel
                if self.planner.daysTraveled < self.planner.lengthOfTravel:
                    last = self.planner.itinerary[-1]
                    endOfDay = "Day ended at " + convertTime(last.currentTime+last.dest.duration+last.mealbreak)
                    endOfDay += " Spent: "+ str(last.currentMoney) +"\n"
                    endOfDay += "\nDay "+str(self.planner.daysTraveled+1)
                    self.addAssignment(endOfDay)
                return


    def solve(self):
        #print "solving ", self.planner.currentDay, self.planner.currentTime
        lunchTime = 12
        dinnerTime = 18
        #assignment = []
        if (self.isComplete()):
            return
        #select variable based on priority
        sortedVariables = sorted(self.variables, cmp = self.compPriority)
        while len(sortedVariables) >0:
            nextDest = sortedVariables[0]
            if self.satisfyConstraints(nextDest):
                #removing from available destinations
                self.variables.remove(nextDest)
                sortedVariables.remove(nextDest)

                #calculating time and mealbreak
                travelTime = self.planner.getTravelTime(self.planner.currentDest,nextDest)
                endTime = self.planner.currentTime+travelTime+nextDest.duration
                mealbreak = False
                if lunchTime>=self.planner.currentTime and lunchTime<=endTime:
                    mealbreak = True
                elif dinnerTime>=self.planner.currentTime and dinnerTime<=endTime:
                    mealbreak = True

                #creating new assignment
                self.planner.moneySpent+=nextDest.cost
                self.planner.currentTime+=travelTime
                newAssign = Assignment(self.planner.currentDay, self.planner.currentTime, self.planner.moneySpent, nextDest, travelTime,mealbreak)
                self.addAssignment(newAssign)

                # updating planner status
                if mealbreak == True:
                    self.planner.currentTime+=1.5
                self.planner.currentTime+=nextDest.duration

                if (self.planner.currentTime > self.planner.endTime):
                    self.incrementDay()
                
                self.planner.currentDest = nextDest

                return self.solve()
            else:
                sortedVariables.remove(nextDest)
            
        return


def shouldEndTravel(problem):
    if (problem.planner.moneySpent >= problem.planner.budgetLimit):
        return True
    if (problem.planner.daysTraveled >= problem.planner.lengthOfTravel):
        return True
    if (len(problem.variables)==0):
        return True

    return False


def input():
    lengthOfTravel = int(raw_input("How many days do you plan to travel? "))
    startDay = raw_input("What day do you plan to begin travelling? (e.g. Mon) ")
    #startTime = int(raw_input("At what time do you want to start travelling? "))
    #endTime = int(raw_input("At what time do you want to return home? "))
    budgetLimit = int(raw_input("What is your budget limit? "))

    interests = []
    temp = raw_input("Are you interested in Outdoor and Adventure? ")
    if (temp == "yes" or temp =="y"):
        interests.append("Outdoor and Adventure")
    temp = raw_input("Are you interested in Events and Amusement? ")
    if (temp == "yes" or temp =="y"):
        interests.append("Events and Amusement")
    temp = raw_input("Are you interested in Culture and Landmarks? ")
    if (temp == "yes" or temp =="y"):
        interests.append("Culture and Landmarks")

    return TravelPlanner(startDay,lengthOfTravel,9,22,budgetLimit,interests,"Hotel",'data2.csv', 'distance2.csv', 'time2.csv')

    

def main():
    #Default:
    planner = TravelPlanner("Fri",3,9,22,300,["Outdoor and Adventure","Events and Amusement","Culture and Landmarks"],"Hotel",'data2.csv', 'distance2.csv', 'time2.csv')

    #planner = input()
    problem = Problem(planner)
    for i in range(1,len(planner.destinations)):
        dest = planner.destinations[i]
        newDest = Destination(dest[0],dest[1],dest[2],dest[3],dest[4],dest[5],dest[6],dest[7],dest[8],dest[9])
        problem.addVariable(newDest)
    problem.addConstraint(planner.constraint)

    problem.addAssignment("Day 1")
    problem.solve()

    print "\nTravel Begin:"
    while (not shouldEndTravel(problem)):
        problem.incrementTime()
        problem.solve()

    for dest in planner.itinerary:
        print dest

    last = planner.itinerary[-1]

    print "Travel ended: " ,last.currentDay, " ", convertTime(last.currentTime+last.dest.duration+last.mealbreak), " Spent: ", last.currentMoney
    print "Went to " , planner.destTraveled, " places, had ", planner.funHad, " fun"
    #print "\nDestinations left: \n"
    #for dest in problem.variables:
    #    print dest

    return

if __name__ == "__main__":
    main()
    



# should add prefer time
# should adjust fun rate?
# event time and tour duration should be fixed -> hard constraint
# tour duration should be fixed
# backtrack? 
# in the same neighborhood, should go together
# think about coming home at night
# too much uncertainty, start and end time can change the schedule a lot, 
# energy consumption
# places with early/late hours are prefered. NOT GOOD???
