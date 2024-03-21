import os
import re
import csv
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from collections import OrderedDict
import sys
import shutil

def subjectName(numberStr):
    number=int(numberStr)
    if(number==1):
        return "vtuber"
    if(number==2):
        return "實況主"
    if(number==3):
        return "政治人物"
    if(number==4):
        return "通告藝人"
    if(number==5):
        return "運動員"
    else:
        return "None" 
def titleName(targetList):
    with open("./Ptt_TargetTable.csv",'r',encoding = 'utf-8-sig',newline = '') as csvfile:
        reader=csv.reader(csvfile)
        firstLine=True
        for row in reader:
            if(firstLine):
                firstLine=False
                continue
            tempList=[]
            tempList.append(row[0])
            tempList.append(subjectName(row[0]))
            tempList.append(row[1])
            tempList.append(row[2])
            targetList.append(tempList)

def getBoard():
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("disable-infobars")
    options.add_argument("--headless")
    driver = webdriver.Chrome('/Users/User/Desktop/chromedriver.exe', options=options)
    driver.get("https://www.ptt.cc/bbs/index.html")

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    boardTitle = soup.findAll('div',{'class','board-name'})

    tagList=[]
    for tag in boardTitle:  
        tagText=tag.text
        tagList.append(tagText)
    driver.close()
    return tagList

def check_element_exists(driver, element, condition):
    try:
        if condition == 'class':
            driver.find_element_by_class_name(element)
        elif condition == 'id':
            driver.find_element_by_id(element)
        elif condition == 'xpath':
            driver.find_element_by_xpath(element)
        return True
    except Exception as e:
        return False

####### 連接網站driver
def connectDriver (target,targetAddress,pageNumber,fullUrl):

    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("disable-infobars")
    options.add_argument("--headless")
    driver = webdriver.Chrome('/Users/User/Desktop/chromedriver.exe', options=options)
    driver.get(targetAddress)
    title=driver.title
    if(title=="批踢踢實業坊"):
        button = driver.find_element_by_class_name("btn-big")
        button.click()
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    ######搜尋目標人物
    if(check_element_exists(driver,"query","class")==False):
        print("No element in "+str(targetAddress))
        return fullUrl
    # 定位搜尋框
    element = driver.find_element_by_class_name("query")
    # 傳入字串
    element.send_keys(target)
    element.send_keys(Keys.ENTER)

    ###### 下方是換爬取的目標網頁

    driver.get(driver.current_url)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    ###### pageNumber是要往前翻頁的次數；fullUrl是存放所有新聞連結的陣列

    # pageNumber=5
    hasNextPage=True
    firstPage=True

    for page in range(pageNumber):

    ###### 下方是將搜尋結果的每個連結取出

        WebLink=soup.findAll('div',{'class','title'})

        for web in WebLink:
            if(web.a!=None):
                newUrl=web.a.get('href')
                fullUrl.append('https://www.ptt.cc'+newUrl)

    ###### nextPage是為了找翻頁的按鈕；nextPage的第二個是按鈕是"上頁"，抓其網址並將driver、soup目標網址換"上頁"的網址

        nextPage = soup.findAll('a',{'class','btn wide'}) 
        Locationcount=0
        nextPageUrl=""

        for location in nextPage:
            ### nextPage不等於4且firstPage=false代表來到最後一頁了，而firstPage則判斷是否為搜尋第一頁，避免翻頁到底再翻回來，所以退出迴圈

            if(len(nextPage)!=4 and firstPage==False):
                hasNextPage=False
                break
            if(Locationcount==1):
                nextPageUrl='https://www.ptt.cc'+location.get('href')
            Locationcount+=1
        if(len(nextPageUrl)<=10):
            break
        firstPage=False

        if(hasNextPage==False):
            break
        #print("the next page is"+str(nextPageUrl))
        driver.get(nextPageUrl)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
    # if(chromNumber==len(tagList)):
    #     return [fullUrl,driver]
    driver.quit()
    return fullUrl



def writeTitle(target,titleID,titleName,article,address,targetNumber):
###### 下面是寫title的csv檔    

    with open(target+'_PttTitle.csv','a',encoding='utf-8-sig',newline='') as csvfile:

        fieldnames = ['TitleID','TitleName','TID','Article','Address']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,dialect="excel")

        if(titleID==1):
            writer.writeheader()

        writer.writerow({'TitleID': titleID, 'TitleName': titleName , 'TID': targetNumber ,'Article': article,'Address':address})
    # print(titleID,titleName,target)
    return titleID+1

##下方是存整個網頁的函式
def writeHtml(titleID,content):
    if(titleID==1):
        os.mkdir(target+"_FullHtml")
    with open("./"+target+"_FullHtml/"+target+"_"+str(titleID)+'_FullHtml.txt','a',encoding='utf-8-sig',newline='') as csvfile:
        fieldnames = ['Html']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,dialect="excel")

        writer.writerow({'Html': content})

##下方是刪除html標籤的函式(如果那行有"<"+">"的話，就整行刪掉)
def deleteHtmlTag(sentence):
    ori_sentenge=sentence.split("\n")
    for word in ori_sentenge: 
        coun=0
        del_check=False
        for w in word:
            if("<"==w or ">"==w):
                coun=coun+1
            if(coun>=2):
                del_check=True
                break
        if(del_check):
            ori_sentenge[ori_sentenge.index(word)]=""
    filter(None,ori_sentenge)
    sentence="\n".join(ori_sentenge)
    sentence=sentence.replace("\n\n\n","\n")
    sentence=sentence.replace("\n\n","\n")
    sentence=sentence.strip()
    return sentence

def visitAllUrl(fullUrl,target,target_row):
    global nothas_header
###### 下方是所有搜尋結果的網址，用迴圈跑過所有網址
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("disable-infobars")
    options.add_argument("--headless")
    if __name__ == "__main__":
        driver = webdriver.Chrome('/Users/User/Desktop/chromedriver.exe', options=options)

    titleID=1
    CIDnumber=1

    # ##以下為測試單一網址用(8/27 https://www.ptt.cc/bbs/C_Chat/M.1649637498.A.D46.html)
    # test=[]
    # test.append("https://www.ptt.cc/bbs/C_Chat/M.1649637498.A.D46.html")
    # fullUrl=test

    if(len(fullUrl)==0):
        print("此查詢沒有結果")
        exit()

    for x in range(len(fullUrl)):
        
        print("Target: "+target+". Now web is "+fullUrl[x]+", is number "+str(x)+" of "+str(len(fullUrl)-1))
        address=fullUrl[x]
        driver.get(fullUrl[x])
        title=driver.title
        if(title=="批踢踢實業坊"):
            button = driver.find_element_by_class_name("btn-big")
            button.click()
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # fullHtml=str(soup)
        


        totalUserid=[]
        totalComment=[]
        totalDateTime=[]
        # totalArticle=[]
        # 抓標題
        title=soup.findAll('span',{'class','article-meta-value'})
        titleCount=0
        titleName=""
        for titleContent in title:

            if(titleCount==2):
                titleName=str(titleContent.text)
                titleName=titleName.replace('[影音]',"").replace('[綜合]',"").replace('[外絮]',"").replace('[輝夜]',"").replace('[標的]',"").replace('[趣事]',"").replace('[kuso]',"").replace('[漫畫]',"").replace('[笑話]',"").replace('[新聞]',"").replace('[問卦]',"").replace('[邊緣]',"").replace('[商品]',"").replace('[消息]',"").replace('[生活]',"").replace('[其他]',"").replace('[出售]',"").replace('[揪團]',"").replace('[公告]',"").replace('[稱讚]',"").replace('[遊記]',"").replace('[實況]',"").replace('[難過]',"").replace('[演員]',"").replace('[正妹]',"").replace('[廣告]',"").replace('[神人]',"").replace('[黑特]',"").replace('[XD]',"").replace('[分享]',"").replace('[交換]',"").replace('[交易]',"").replace('[ＸＤ]',"").replace('[戰場]',"").replace('[推薦]',"").replace('[牌組]',"").replace('[贈送]',"").replace('[請益]',"").replace('[討論]',"").replace('[地獄]',"").replace('[猜謎]',"").replace('[耍冷]',"").replace('[瓦特]',"").replace('[取暖]',"").replace('[姆咪]',"").replace('[尋協]',"").replace('[徵求]',"").replace('[情報]',"").replace('[問題]',"").replace('[爆卦]',"").replace('[心得]',"").replace('[閒聊]',"").replace('[創作]',"").replace('Re:',"").strip()
            titleCount+=1

        # 抓文章內容
        # article_html=soup.findAll('div',{'bbs-screen bbs-content'})
        # str_article=str(article_html)
        # pre_article=str_article.split("--")[:-1]
        # half_article="--".join(pre_article)
        # #這邊的迴圈是把--不只一組的情況，只取第一組有文章內容的，其他刪掉
        # delete_flag=True
        # while(delete_flag):
        #     if(len(pre_article)>1):
        #         pre_article=half_article.split("--")[:-1]
        #         half_article="--".join(pre_article)
        #     else:
        #         delete_flag=False
        # article_delete_first_line=half_article.split("\n")[1:]
        # article="\n".join(article_delete_first_line)
        #用deleteHtmlTag把tag清除
        # final_article=deleteHtmlTag(str(article))
        #把最後結果加入totalArticle的list中
        # totalArticle.append(final_article)
            
        # 抓作者
        userid=soup.findAll('span',{'class','f3 hl push-userid'})
        for userName in userid:
            userName=str(userName.text).strip()
            # print(userName)
            totalUserid.append(userName)

        # 抓內容
        comment=soup.findAll('span',{'class','f3 push-content'})
        for commentContent in comment:
            commentContent=str(commentContent.text).strip()
            commentContent=commentContent[1:]
            commentContent=commentContent.strip()
            totalComment.append(commentContent)

        # 抓時間
        dateYear=soup.findAll('span',{'class','article-meta-value'})
        yearDate=0
        compare_time=""
        global input_time_stamp
        global input_time2_stamp
        if(len(dateYear)>=4):
            yearTimeTemp=dateYear[3].text
            yearTime=yearTimeTemp.replace("  "," ").split(" ")

            compare_time=yearTime[4]+"-"+yearTime[1]+"-"+yearTime[2]
            struct_time = time.strptime(compare_time, "%Y-%b-%d") # 轉成時間元組
            compare_stamp=time.mktime(struct_time)
            if(compare_stamp < input_time_stamp or compare_stamp > input_time2_stamp): #如果抓到的時間小於所要的時間，則continue繼續下一個
                continue
            # time.sleep(1)
            #底下判定是為了有些文章時間只有日期加月份而無年分，故直接將年分改為2022
            if(len(yearTime)>=4):
                yearDate=yearTime[4]
            else:
                continue
        else:
            continue
        dateTime=soup.findAll('span',{'class','push-ipdatetime'})
        for ipDate in dateTime:
            ipDate=str(ipDate.text).strip()
            temp=[]
            temp=ipDate.split(" ")
            # 有ip、時間
            if(len(temp)==3):
                ipDate=temp[1]+" "+temp[2]
            # 沒有ip，只有時間
            elif(len(temp)==1):
                ipDate=temp[0]
            else:
                ipDate=temp[0]+" "+temp[1]
            ipDate=yearDate+"/"+ipDate
            totalDateTime.append(ipDate)

        with open('renew_PttContent3.csv','a',encoding='utf-8-sig',newline='') as csvfile:
            # 定義欄位
            fieldnames = ['Platform','SID','SName','TID','TName','TitleID','Title','Url','CID','CName', 'Comment', 'DateTime']

            # 將 dictionary 寫入 CSV 檔
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames,dialect="excel")

            # 寫入第一列的欄位名稱
            if(nothas_header):
                nothas_header=False
                writer.writeheader()

            sameIDCound=0
            for number in range(len(totalUserid)):
                
                next=number+1
                CIDnumber+=1
                if(next!=len(totalUserid)):
                    if(totalUserid[next]==totalUserid[number]):
                        totalComment[next]=totalComment[number]+totalComment[next]
                        sameIDCound+=1
                        CIDnumber-=1
                        continue
                # 如果沒有標題(但可能沒標題有評論)，則將標題取為None
                if(len(titleName)==0):
                    titleName="None"
                if("img" in str(totalComment[number]) or "jpg" in str(totalComment[number]) or "png" in str(totalComment[number]) or "gif" in str(totalComment[number])):
                    continue
                writer.writerow({'Platform':"0",'SID':target_row[0],"SName":subjectName(target_row[0]),"TID":target_row[2],"TName":target,'TitleID': titleID,"Title":titleName,"Url":address, 'CID': CIDnumber-1, 'CName': str(totalUserid[number]), 'Comment': str(totalComment[number]), 'DateTime': str(totalDateTime[number])})

                # 如果沒有評論則不寫入檔案
            titleID+=1
                    # writeHtml(titleID,fullHtml)
                    # titleID=writeTitle(target,titleID,titleName,final_article,address,targetNumber)
    ###### 爬蟲到這邊


        
        ###### 下方決定要抓幾篇

        # if(titleID==grabNumber):

        #     break       
        # driver.close()
    driver.quit()

####### target=目標；grabNumber=要抓的新聞數量；pageNumber要往前翻的頁數(一頁最多會有20篇新聞)


def startProgram(target,pageNumber,target_row):
    if __name__=="__main__":
        tagList=getBoard()
    fullUrl=[]
    for tag in tagList:
        ##這邊是把各版的tag(ex:gossipin、c_chat等抓取)
        targetAddress="https://www.ptt.cc/bbs/"+tag+"/"
        fullUrl=connectDriver(target,targetAddress,pageNumber,fullUrl)
        # fullUrl=tempList
        # ##下面的break是測試用的，加了break代表只去八卦版中做搜尋，並爬搜尋結果的網址
        # break
    removeRepeatFullUrl= list(OrderedDict.fromkeys(fullUrl))

    visitAllUrl(removeRepeatFullUrl,target,target_row)

    


###0916

def createDataFrame(subjectList):
    sid=1
    subjectDataFrame = {}
    for subject in range(len(subjectList)):
        subjectDataFrame[subjectList[subject]] = sid
        sid+=1 
    return subjectDataFrame

###### 下面是寫Subect的csv檔 
def writeSubject(SID,subject):
    with open('Ptt_SubjectTable.csv','a',encoding='utf-8-sig',newline='') as csvfile:

        fieldnames = ['SID','Subject']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,dialect="excel")

        if(SID==1):
            writer.writeheader()

        writer.writerow({'SID': SID,'Subject':subject})

###### 下面是寫TargetTable的csv檔  
def writeTargetTable(SID,TID,TargetName):
    with open('Ptt_TargetTable.csv','a',encoding='utf-8-sig',newline='') as csvfile:

        fieldnames = ['SID','TID','TargetName']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,dialect="excel")

        if(TID==1):
            writer.writeheader()

        writer.writerow({'SID': SID,'TID':TID,'TargetName':TargetName})

def renewSubjectTable(subject_SID,subject_subject):
    with open('Ptt_SubjectTable.csv',newline='',encoding="utf-8" ) as csvfile:
        rows = csv.reader(csvfile)
        con=0
        for row in rows:
            if(con==0):
                con+=1
                continue   
            subject_SID.append(row[0])
            subject_subject.append(row[1])

def renewTargetTable(target_SID,target_TID,target_targetName):
    with open('Ptt_TargetTable.csv',newline='',encoding="utf-8" ) as csvfile:
        rows = csv.reader(csvfile)
        con=0
        for row in rows:
            if(con==0):
                con+=1
                continue  
            target_SID.append(row[0])
            target_TID.append(row[1])
            target_targetName.append(row[2])

def targetCheck(target_TID,target_targetName,originTarget):
    for number in range(len(target_targetName)):
        if(target_targetName[number] == originTarget):
            targetNumber=target_TID[number]
            return targetNumber
    targetNumber=int(target_TID[-1])+1
    return targetNumber

########主程式開始位置

targetList=[]
titleName(targetList)

# pageNumber=int(input("請輸入要搜尋的頁數："))
# 下面的pageNumber是代表要翻頁的頁數，一頁最多會有20篇文章，以1000頁作為預設上限，nothas_header代表這個檔案還沒有header
pageNumber=200
target=""
input_time="2022/09/01"
input_time2="2022/10/31"
nothas_header=True
time_temp= time.strptime(input_time, "%Y/%m/%d")
input_time_stamp=int(time.mktime(time_temp))
time_temp2= time.strptime(input_time2, "%Y/%m/%d")
input_time2_stamp=int(time.mktime(time_temp2))
# !!!!!!!!!!!!!!!!!!!! 前置作業 !!!!!!!!!!!!!!!!!!!!!!!!!
# 1.設定好要翻頁的頁數(pageNumber)
# 2.把要爬的目標放入targetList
# 3.確定此程式的當前路徑沒有目標列表的資料夾(若有刪掉其資料夾即可，此程式會創立一新的資料夾)
# 4.把目標的targetType設定好
# 5.把targetList填滿
# 注意 : 檢查是否將startProgram()函式中的 break註解，以及是否將現存路徑的目標資料夾清空

#---------------------資料陣列
# subject_SID=[]
# subject_subject=[]

# target_SID=[]
# target_TID=[]
# target_targetName=[]

# renewSubjectTable(subject_SID,subject_subject)
# renewTargetTable(target_SID,target_TID,target_targetName)
#---------------------

#只需要改targetType、targetList的參數就可以了
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#targetType是subject名稱
# targetType="temp"
# originTargetType=targetType

# 把目標放入targetList
# targetList=["高虹安"]
# target=targetList[0]
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#exceptList存放在爬蟲期間，有出現錯誤的目標
exceptList=[]

tempList=[39]
# 若要看爬蟲時出現了什麼錯誤，把try那行註解，再把包含except以下的內容全部註解，再次執行程式即會顯示錯誤
for i in range (1):#要抓80人的時候把左邊改成len(targetList)
    # os.mkdir(target)創建當前目標的資料夾
    # os.chdir(target)切換路徑至方才創建的資料夾
    # 爬完後os.chdir(original_Path)回到初始路徑
    #!!
   try:
        #把target設定為從targetList裡面的內容
        target=targetList[tempList[i]-1][3]
        target_row=targetList[tempList[i]-1]
        
        print("Now target: "+target)
        if __name__ == "__main__":
            startProgram(target,pageNumber,target_row)
        
    # 若在爬蟲出現錯誤時，會把路徑切換回初始路徑，並且把出現錯誤的目標記錄到exceptList中
    # count變數是為了計算是否還有未抓過的目標，若沒有時，會透過指令sys.exit(0)將程式結束
    # 若還有目標為抓過，此時暫停20秒後，跳過此目標，繼續下一個目標的爬取
    #!!
   except:
        print("Error!!")
        
        #回到currentSubject_Path，並刪除剛剛出錯的資料夾
        # os.chdir(currentSubject_Path)
        # os.remove(currentSubject_Path+"\\"+target)
        # shutil.rmtree (currentSubject_Path+"\\"+target)
        # print("刪除 "+currentSubject_Path+"\\"+target)

        #回到有存放Ptt_TargetTable.csv的路徑
        # os.chdir(currentSubject_Path)

        #加入出錯的target到exceptList內
        exceptList.append(target)
        # count=i
        # if(count+2>len(targetList)):
            # print("There are zero target to find !!")
            # print("The exceptList is : ",exceptList)
            # sys.exit(0)
        time.sleep(10)
        continue

print(exceptList)
