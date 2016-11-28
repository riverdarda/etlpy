
# coding=utf-8
import sys,os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/src'
sys.path.insert(0,parentdir)
from spider import *
from repl import  *
import extends
extends.enable_progress=False
import requests
# In[2]:
execute= False
if len(sys.argv)>1 and sys.argv[1]=="true":
    execute = True


def get_xpath(s):
    if s=='guokr':
        return '//div[1]/div'
    else:
        return None


def get_content(s):
    if 'content' in s:
        s['content'] = s['content'][0]["value"]
    elif 'desc' in s:
        s['content'] = s['desc']

    elif 'summary' in s:
        s['content'] = s['summary']
    return

def get_hash(s):
    t=hash(s['title']+s['link'])
    s['hash']=t

# In[42]:

mongo=get_default_connector()
mongo.db="ant_temp"
table_name='life_rss_online'
table_name_all='life_rss_all'
count_per_id= 5
#remote='http://recproxy.cz00b.alipay.net/recommend.json?_sid_=44040'
remote='http://recproxy-pre.alipay.com/recommend.json?_sid_=9457'


# In[4]:

import feedparser


# In[5]:

rlist=requests.get(remote+'&invoke_method=get_rss_list')
rlist=rlist.json()
rlist= rlist.get('rss_list','')

if rlist=='':
    print 'get rss list empty ,quit'
    exit()

rlist2=[];
for item in rlist.split('\n'):
    kv= item.split('\t')
    if len(kv)<2:
        continue
    k=kv[0].strip()
    v=kv[1].strip()
    rlist2.append({'app_id':k,'rss':v})

#print rlist2

ins= task('insert')
ins.nullft('error',revert=True)
ins.dbex(sl='mongo',table=table_name)

rss = task('rss')
# rss.pyge('rss',sc=[r for r in rss_list.split('\n') if r!='' and r.startswith('#')==False])
rss.pyge(sc=[r for r in rlist2])
#rss.matchft('rss', sc='haibao', mode='re',revert=True)
rss.split('rss:source',  sc='.' ).at('source',sc='1')
rss.py('source:xpath', sc=get_xpath)
rss.py('rss', sc=lambda d: feedparser.parse(d)['entries'][:count_per_id]).list(sc='source xpath app_id').dict()
rss.py( sc=get_hash)
rss.nullft('hash')
if  True:#True: #True:#execute:
    rss.joindb('hash', sl='mongo', table=table_name, sc='title:title2', mode='doc')
    rss.nullft('title2', revert=True)
rss.py(sc=get_content)
rss.keep('author,hash,content,description:desc,published:publish_time,link,title,source,xpath,app_id')
rss.xpath('content', sc='[xpath]', mode='html').html(mode='decode').pyft( sc='len(content)>100')
rss.replace('content', sc='https://', new_value='http://')
rss.replace(sc='href=\".*?\"',new_value='',mode='re')
rss.replace(sc='<img src="http://ocpk3ohd2.qnssl.com/rss_bottom.jpg" />',new_value='',mode='str')
rss.xpath('content:cover', sc='//img[1]/@src')
rss.nullft('cover').pyft('cover',sc='len(value)<300')
rss.matchft('cover', mode='re', sc='data:', revert=True).matchft( mode='re', sc='http:')
rss.replace( sc='https', new_value='http')
#rss.addnew('app_id', sc='2016092601973157')
rss.addnew('r_url', sc=remote)
rss.addnew('invoke_method', sc='send')
rss.addnew('comment', sc='true')
rss.addnew('liked', sc='true')
rss.delete('xpath')
rss.repeatft('title')
rss.rename('source:author,link:url')
if execute:
    rss.dict('post', sc="title desc liked comment content cover url app_id invoke_method")
    rss.crawler('r_url:resp', sc='[post]',mode='post')
    rss.json('resp', mode='decode').dict()
rss.dbex(sl='mongo',table=table_name_all)
rss.etlex(sl='insert')
#result=rss.get(10)


send_result=rss.get(500,etl=100,execute=execute,format='df')
#rss.check()
#rss.get(etl=100)
print send_result[['title','url','hash']]





