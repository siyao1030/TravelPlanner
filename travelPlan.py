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
    def __init__(self, name, description=None, category=None, address=None, cost=None, openHour=None, closeHour=None, closedDays=None, duration=None, scale=None):
        self.name = name
        self.description = description
        self.category = category
        self.address = address
        self.cost = cost
        self.openHour = openHour
        self.closeHour = closeHour
        self.closedDays = closedDays
        self.duration = duration
        self.scale = scale

        self.priorityScore = 0


    
    def __repr__(self):
        s = "Destination: " + self.name + "\n" + "Address: " + self.address + "\n" 
        s += "Cost: " + str(self.cost) + "\n" + "Duration: "+ str(self.duration)+ "\n" 
        s += "Open Hours: " + convertTime(self.openHour) + "-" + convertTime(self.closeHour) + "\n"
        s += "Closed on: " + str(self.closedDays) + "\n"
        return s



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
        #["Outdoor and Adventure", "Event and Amusment", "Culture and Landmarks"]

        #self.startDest = startDest
        self.destinations = self.getDestinations(destCSV)
        #dest = next(x for x in self.destinations if x[0] == startDest)
        #self.startDest = Destination(dest[0],dest[1],dest[2],dest[3],dest[4],dest[5],dest[6],dest[7],dest[8],dest[9])
        self.travelMatrix = self.getTravelMatrix(timeCSV, distCSV)

        self.currentTime = startTime
        self.currentDay = startDay
        self.moneySpent = 0
        self.daysTraveled = 0
        self.currentDest = self.hotel


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
        #print destA, destB
        return float(self.travelMatrix[(destA.name,destB.name)][0])


    def getDestinations(self, destCSV):
        data=list(csv.reader(open(destCSV,'rb'),delimiter=','))
        for i in range(1,20):
            data[i][4]=float(data[i][4])
            data[i][5]=float(data[i][5])
            data[i][6]=float(data[i][6])
            data[i][8]=float(data[i][8])
            data[i][9]=float(data[i][9])
            data[i][7]=data[i][7].split(",")
        return data


    def getPriorityScore(self, destB, costWeight = 2, funWeight = 0.3, timeWeight = 1, durationWeight = 1):
        score = 10
        # budget
        score -= destB.cost/self.budgetLimit * costWeight
        # fun
        score += destB.scale/10 * funWeight
        # time
        travelTime = self.getTravelTime(self.currentDest, destB)
        timeWasted = max(0, destB.openHour-self.currentTime-travelTime)
        score -= (travelTime+timeWasted)/destB.duration * timeWeight

        timeLeft = self.endTime-self.currentTime
        score -= (travelTime+timeWasted)/timeLeft * timeWeight
        # duration
        actualDuration = min(destB.closeHour - (self.currentTime+travelTime),destB.duration)
        score += actualDuration/destB.duration * durationWeight

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
                if self.daysTraveled < self.lengthOfTravel:
                    print "Day ", self.daysTraveled+1
                return

    #def printResult():

class Assignment(object):
    def __init__(self, dest, currentDay ,currentTime, currentMoney,travelTime):
        self.dest = dest
        self.currentDay = currentDay
        self.currentTime = currentTime
        self.currentMoney = currentMoney
        self.travelTime = travelTime

    def __repr__(self):
        s = "Travel Time: "+ convertTime(self.travelTime) + "\n"
        s += self.currentDay + " "+ convertTime(self.currentTime) #+ " Spent: "+ str(self.currentMoney) + "\n"
        s += "\n" + str(self.dest)
        #return s
        return self.dest.name
        

class Problem:
    def __init__(self, planner):
        self.planner = planner
        self.numDest = 0
        self.variables = []
        self.constraints = []

    def compPriority(self,destx,desty):
        xP = int(self.planner.getPriorityScore(destx)*100)
        yP = int(self.planner.getPriorityScore(desty)*100)
        return yP - xP

    def addVariable(self,variable):
        self.variables.append(variable)
        self.numDest +=1

    def addConstraint(self,constraint):
        self.constraints.append(constraint)

    def isComplete(self,assignment):
        #print "assignment num: ", len(assignment)
        if (self.planner.moneySpent >= self.planner.budgetLimit):
            return True
        if (self.planner.daysTraveled >= self.planner.lengthOfTravel):
            return True
        if (len(self.variables)==0):
            return True
        else:
            return False

    def satisfyConstraints(self, variable):
        for constraint in self.constraints:
            if (not constraint(variable)):
                return False

        return True


    def solve(self):
        assignment = []
        if (self.isComplete(assignment)):
            return assignment
        #select variable based on priority
        sortedVariables = sorted(self.variables, cmp = self.compPriority)
        #print "new iteration, variables left", len(self.variables) ,  "sortedV ", len(sortedVariables)

        while len(sortedVariables) >0:
            
            nextDest = sortedVariables[0]
            if self.satisfyConstraints(nextDest):
                #print "satisfied! ", nextDest.name
                self.variables.remove(nextDest)
                travelTime = self.planner.getTravelTime(self.planner.currentDest,nextDest)
                self.planner.currentTime+=travelTime
                newAssign = Assignment(nextDest, self.planner.currentDay, self.planner.currentTime, self.planner.moneySpent,travelTime)
                assignment.append(newAssign)

                # updating planner status
                self.planner.currentTime+=nextDest.duration
                if (self.planner.currentTime > self.planner.endTime):
                    self.planner.incrementDay()
                self.planner.moneySpent+=nextDest.cost
                self.planner.currentDest = nextDest

                return assignment + self.solve()
            else:
                #print "did not satisfy, removing ", nextDest.name
                sortedVariables.remove(nextDest)
                #print "after removing ", len(sortedVariables), " left"
            
        #print "should be returning, ", len(sortedVariables)
        return assignment




planner = TravelPlanner("Fri", 3, 8, 22, 200, ["Outdoor and Adventure", "Culture and Landmarks"], "Griffith Park", 'data.csv', 'distance.csv', 'time.csv')

def constraint(dest):
    travelTime = planner.getTravelTime(planner.currentDest, dest)
    maxWaitTime = 0.5
    if planner.currentTime+travelTime + maxWaitTime < dest.openHour:
        #print "not open"
        return False
    if planner.currentTime+travelTime + dest.duration > dest.closeHour:
        #print "closed" 
        return False
    if planner.currentDay in dest.closedDays: 
        #print "closed on ", planner.currentDay
        return False
    if planner.moneySpent+dest.cost > planner.budgetLimit:
        #print "exceed budget" 
        return False
    if dest.category not in planner.interests:
        #print "not interested" 
        return False
    if planner.daysTraveled > planner.lengthOfTravel:
        #print "exceed lengthOfTravel"
        return False

    return True


def shouldEndTravel(problem):
    if (planner.moneySpent >= planner.budgetLimit):
        return True
    if (planner.daysTraveled >= planner.lengthOfTravel):
        return True
    if (len(problem.variables)==0):
        return True

    return False

def main():
    problem = Problem(planner)
    for i in range(1,len(planner.destinations)):
        dest = planner.destinations[i]
        newDest = Destination(dest[0],dest[1],dest[2],dest[3],dest[4],dest[5],dest[6],dest[7],dest[8],dest[9])
        problem.addVariable(newDest)
    problem.addConstraint(constraint)

    print "Travel Begin:"
    print "Day 1"
    solutions = problem.solve()
    for assignment in solutions:
        print assignment

    while (not shouldEndTravel(problem)):
        planner.incrementTime()
        newAssign = problem.solve()
        for assignment in newAssign:
            print assignment
        solutions+=newAssign
        #print solutions

    #for assignment in solutions:
     #   print assignment
    #print solutions
    last = solutions[-1]

    print "Travel ended: " ,last.currentDay, " ", convertTime(last.currentTime+last.dest.duration), " Spent: ", last.currentMoney

    print "\nDestinations left: \n"
    for dest in problem.variables:
        print dest

if __name__ == "__main__":
    main()
    



# should add prefer time
# should adjust fun rate?
# user input
# meal time
# event time and tour duration should be fixed -> hard constraint
# tour duration should be fixed
# backtrack?



