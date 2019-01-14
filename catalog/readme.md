# Item Catalog
Modern web applications perform a variety of functions and provide amazing features and utilities to their users

# Prerequisites:-
- Python  [here](https://www.python.org)
- Vagrant   [here](https://www.vagrantup.com/downloads.html)
- VirtualBox   [here](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)

# Instructions:
1.After installing all the Prerequisites Create an empty folder  to hold the project files.
2.clone the project files using ```$ git clone ```                   
3.Run your command-line (cmd,pwoershell,bash, git bash �) and change the path to the directory of the project folder in step 1 using ```$ cd  path_of_the_project_folder```    
4.run the command ```$ vagrant up``` command and wait till it finish.      
5.Download datafile "newsdata.sql" [here](https://d17h27t6h515a5.cloudfront.net/topher/2016/August/57b5f748_newsdata/newsdata.zip).       
6.Unzip "newsdata.zip" and copy "newsdata.sql" to our project folder.
7.Run ```$ vagrant ssh``` inside project folder.   
8.cd to vagrant directory using command ```$ cd /vagrant```.    
9.Fill database from "newsdata.sql" file using this command ```$ psql -d news -f newsdata.sql```.   
10.Now VM machine and database with data are ready.   

# views in the database
* ## topView
<span style="color:white">it is used to get the top titles based on the views</span>  
```
create view topView as   
   select articles.title,count(*) as total_view
   from log , articles,authors    
   where articles.slug=substr(log.path,10)
   and log.status='200 OK'
   group by articles.title order by total_view desc;
```

* ## topAuthor
<span style="color:white">it is used to get the top Author  based on the views</span>
```
create view topAuthor as
   select authors.name,count(*) as total_view
   from articles, authors,log   
   where log.status='200 OK' and articles.slug=substr(log.path,10)
   and articles.author=authors.id
   group by authors.name order by total_view desc;
```


* ## percentege
 <span style="color:white">it is used to get the percentage of error of each day</span>   
 ```
 create view percentege as   
   select time::date as Day_date ,
   ((sum(case when status !='200 OK' then 1 else 0 end)*100.0/count(*)*1.0))    
   as per from log group by time::date;
 ```


# Running the queries:
  1. From the vagrant directory inside the virtual machine,run Logs_Analysis.py using:
  ```
    $ python3 Logs_Analysis.py
  ```


# Note:
- always make sure you are running your command in vagrant VM directory
- to reconnect to the news database You can connect using this command ```psql -d news```
- when you are stuck always use \? command
- when you are performing  sql query do not forget to use ```;``` at the end of every query)
- To close connection with "news" database and return to vagrant VM use press "Ctrl+Z".
