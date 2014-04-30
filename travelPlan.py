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
        #["Outdoor and Adventure", "Event and Amusement", "Culture and Landmarks"]

        self.destinations = self.getDestinations(destCSV)
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

    def constraint(self,dest):
        travelTime = self.getTravelTime(self.currentDest, dest)
        maxWaitTime = 0.5
        if self.currentTime+travelTime + maxWaitTime < dest.openHour:
            #print "not open"
            return False
        if self.currentTime+travelTime + dest.duration > dest.closeHour:
            #print "closed" 
            return False
        if self.currentDay in dest.closedDays: 
            #print "closed on ", planner.currentDay
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

        return True

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
        if timeLeft == 0:
            score -= 1
        else:
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
        return s
        #return self.dest.name
        

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

    def isComplete(self):
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
        #print "solving"
        lunchTime = 12
        dinnerTime = 6
        assignment = []
        if (self.isComplete()):
            return assignment
        #select variable based on priority
        sortedVariables = sorted(self.variables, cmp = self.compPriority)
        while len(sortedVariables) >0:
            nextDest = sortedVariables[0]
            if self.satisfyConstraints(nextDest):
                self.variables.remove(nextDest)
                travelTime = self.planner.getTravelTime(self.planner.currentDest,nextDest)
                endTime = self.planner.currentTime+travelTime+nextDest.duration
                mealbreak = False
                if lunchTime>=self.planner.currentTime and lunchTime<=endTime:
                    mealbreak = True
                elif dinnerTime>=self.planner.currentTime and dinnerTime<=endTime:
                    mealbreak = True

                newAssign = Assignment(self.planner.currentDay, self.planner.currentTime, self.planner.moneySpent, nextDest, travelTime,mealbreak)
                assignment.append(newAssign)

                # updating planner status
                if mealbreak == True:
                    self.planner.currentTime+=1.5
                self.planner.currentTime+=nextDest.duration
                if (self.planner.currentTime > self.planner.endTime):
                    self.planner.incrementDay()
                self.planner.moneySpent+=nextDest.cost
                self.planner.currentDest = nextDest

                return assignment + self.solve()
            else:
                sortedVariables.remove(nextDest)
            
        return assignment


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
    startDay = raw_input("What week day do you plan to begin travelling? ")
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

    return TravelPlanner(startDay,lengthOfTravel,8,22,budgetLimit,interests,"Hotel",'data.csv', 'distance.csv', 'time.csv')

    

def main():
    #Default:
    #planner = TravelPlanner("Fri",3,8,22,200,["Outdoor and Adventure", "Event and Amusement", "Culture and Landmarks"],"Hotel",'data.csv', 'distance.csv', 'time.csv')

    planner = input()
    problem = Problem(planner)
    for i in range(1,len(planner.destinations)):
        dest = planner.destinations[i]
        newDest = Destination(dest[0],dest[1],dest[2],dest[3],dest[4],dest[5],dest[6],dest[7],dest[8],dest[9])
        problem.addVariable(newDest)
    problem.addConstraint(planner.constraint)

    solutions = problem.solve()
    print "\nTravel Begin:"
    print "Day 1"
    for assignment in solutions:
        print assignment

    while (not shouldEndTravel(problem)):
        planner.incrementTime()
        newAssign = problem.solve()
        for assignment in newAssign:
            print assignment
        solutions+=newAssign

    last = solutions[-1]

    print "Travel ended: " ,last.currentDay, " ", convertTime(last.currentTime+last.dest.duration+last.mealbreak), " Spent: ", last.currentMoney

    print "\nDestinations left: \n"
    for dest in problem.variables:
        print dest


    

    return

if __name__ == "__main__":
    main()
    



# should add prefer time
# should adjust fun rate?
# user input
# meal time
# event time and tour duration should be fixed -> hard constraint
# tour duration should be fixed
# backtrack?



