import requests, urllib
from bs4 import BeautifulSoup
import re
import pandas


#####################################

# 使用说明:

# - 功能:
# 将本python文件和包含文章标题的txt文件放于同一文件夹，python将在知网挨个搜索论文标题，并获取第一项结果的“中国期刊全文数据库”引文信息，包括标题、作者、单位、摘要、基金、关键词等信息，最终输出为excel文档

# - 使用方法:
# 仅需修改两项参数：
# article_txt_read 为需要读取的txt文档，文档内容为按行排列的论文标题
# part_article_out 为最终输出的excel文档

#####################################

article_txt_read = '1.txt'
final_article_out = '2.xlsx'

part_article_out = '1.xlsx'


# 正则表达式获取每篇引文的链接地址
filename = re.compile(r'''filename=(.*)&amp;dbcode''')
dbname = re.compile(r'''dbname=(.*)&amp;v=''')
# 正则表达式获取检索页面中第一篇文章链接地址
article_url = re.compile(r'''<a href="(.*)" target=''')
quote_url = re.compile(r'''value="(.*)"/>''')
dbcode = re.compile(r'''dbname=(.*)''')
filename = re.compile(r'''filename=(.*)&amp;''')
dbname = re.compile(r'''dbname=(.*)&amp;''')
filename2 = re.compile(r'''filename=(.*?)&''')
dbname2 = re.compile(r'''dbname=(.*)&filename=''')
if_CJFD = re.compile('CJFD')

# 新建列表，用于存储引文的多项信息
result_list = {
    "orgtitle": [],
    "title": [],
    "author": [],
    "orgn": [],
    "ChDivSummary": [],
    "catalog_FUND": [],
    "catalog_KEYWORD": [],
    "catalog_ZCDOI": [],
    "catalog_ZTCLS": []
}

total = []
invalid_article = []
invalid_article_org = []
lost_quote_article = []


# 获取引文页面的标题、作者、机构、摘要、基金*、关键词、DOI*、分类号这8项信息
def get_detail(url):
    res = requests.get(url)
    res.encoding = 'utf - 8'
    soup = BeautifulSoup(res.text, 'html.parser')

    try:
        title = soup.select('.title')[0].text
    except:
        title = ''
    try:
        author = soup.select('.author')[0].text
    except:
        author = ''
    try:
        orgn = soup.select('.orgn')[0].text
    except:
        orgn = ""

    try:
        ChDivSummary = soup.select('#ChDivSummary')[0].text
    except:
        ChDivSummary = ''

    try:
        catalog_FUND = soup.select('#catalog_FUND')[0].text
    except:
        catalog_FUND = ''

    if catalog_FUND:
        catalog_FUND = soup.select('p')[3].text[3:].replace(' ', '').replace('\r', '').replace('\n', '')
        catalog_KEYWORD = soup.select('p')[4].text[4:].replace(' ', '').replace('\r', '').replace('\n', '')
        try:
            catalog_ZCDOI = soup.select('#catalog_ZCDOI')[0].text
        except:
            catalog_ZCDOI = ''
            catalog_ZTCLS = soup.select('p')[5].text[4:]
        else:
            catalog_ZCDOI = soup.select('p')[5].text[4:]
            catalog_ZTCLS = soup.select('p')[6].text[4:]

    else:
        catalog_KEYWORD = soup.select('p')[3].text[4:].replace(' ', '').replace('\r', '').replace('\n', '')
        try:
            catalog_ZCDOI = soup.select('#catalog_ZCDOI')[0].text[4:]
        except:
            catalog_ZCDOI = ''
            catalog_ZTCLS = soup.select('p')[4].text[4:]
        else:
            catalog_ZCDOI = soup.select('p')[4].text[4:]
            catalog_ZTCLS = soup.select('p')[5].text[4:]

    result_list["article_detail"].append(
        dict(orgtitle=orgtitle, title=title, author=author, orgn=orgn, ChDivSummary=ChDivSummary,
             catalog_FUND=catalog_FUND, catalog_KEYWORD=catalog_KEYWORD, catalog_ZCDOI=catalog_ZCDOI,
             catalog_ZTCLS=catalog_ZTCLS))

def bs4(url):
    res = requests.get(url)
    res.encoding = 'utf - 8'
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup

# 通过正则表达式合成每篇引文地址的特征信息，返回引文链接
def output_url(seleted_soup):
    filename1 = filename.search(str(seleted_soup))
    dbname1 = dbname.search(str(seleted_soup))
    literature_url = str('http://kns.cnki.net/kcms/detail/detail.aspx?filename=' + filename1.group(
        1) + '&dbcode=CJFQ&dbname=' + dbname1.group(1) + '&amp;v=')

    return literature_url



#第一次抓取
m = 0
n = 0
x = 0
for line in open(article_txt_read):

    result_list["article_detail"] = [0, ]

    m += 1
    # if m == 40:
    #     break

    i = 0
    for cha in str(line):
        if '\u4e00' <= cha <= '\u9fff':
            orgtitle = line
            break
        else:
            i += 1

    print('No%d:%s' % (m, orgtitle),end='')
    orgtitle_noLF = orgtitle.replace('\n','')

    # 生成以每篇文章作为关键字的检索页面,并产生第一篇文章的链接
    base_url = 'http://scholar.cnki.net/result.aspx?q=' + urllib.parse.quote(orgtitle) + '&rt=&rl=&udb='


    try:
        article = bs4(base_url).select('.gotodetaillink')[0]   #选择检索页面的第几篇
    except (IndexError):
        n += 1
        invalid_article_org.append(orgtitle_noLF)
        #print(invalid_article)
        continue

    first_article_url = str(article_url.search(str(article)).group(1)).replace('&amp;', '&').replace('\r', '').replace('\n', '')

    print(first_article_url)


    # 从指定文章的源代码提取其引文的关键信息，并生成引文链接
    try:
        value = bs4(first_article_url).select('#listv')[0]
        value1 = quote_url.search(str(value)).group(1)
        dbcode1 = dbcode.search(str(first_article_url)).group(1)[:4]
        filename3 = filename2.search(str(first_article_url)).group(1)
        dbname3 = dbname2.search(str(first_article_url)).group(1)
    except:
        n += 1
        invalid_article_org.append(orgtitle_noLF)
        #print(invalid_article)
        continue

    quote_final_url = 'http://www.cnki.net/kcms/detail/frame/list.aspx?dbcode=' + dbcode1 + '&filename=' + filename3 + '&dbname=' + dbname3 + \
                      '&RefType=1&vl=' + value1
    print(quote_final_url)
    # 获取引文的篇数
    try:
        num = int(bs4(quote_final_url).select('.count')[0].text.replace(' ', '')[5: -3])
    except:
        n += 1
        invalid_article_org.append(orgtitle_noLF)
        #print(invalid_article)
        continue

    result_list["article_detail"] = [
        dict(orgtitle='', title='', author='', orgn='', ChDivSummary='', catalog_FUND='', catalog_KEYWORD='',
             catalog_ZCDOI='', catalog_ZTCLS='')]






    # 用于检测是否存在CJFD(中国学术期刊网络出版总库）
    try:
        CJFD = bs4(quote_final_url).select('.dbName')[0]
        # print(CJFD)
    except:
        n += 1
        invalid_article_org.append(orgtitle_noLF)
        # print(final_invalid_article)
        continue

    CJFD_exist = re.findall(r"中国期刊全文数据库", str(CJFD.text))

    if CJFD_exist:
        CJFD_url = quote_final_url + '&CurDBCode=CJFD'
        # print(CJFD_url)
        num = int(bs4(quote_final_url).select('.count')[0].text.replace(' ', '')[5: -3])
        # print(num)

        if num != 0:
            pass
        else:
            n += 1
            lost_quote_article.append(orgtitle)
            # print(final_invalid_article)
            continue
    else:
        n += 1
        lost_quote_article.append(orgtitle)
        continue

    if num >= 1 and num <= 10:
        i = 0
        for i in range(0, num):
            try:
                lv = bs4(CJFD_url).select('a[target="_blank"]')[i]
            except:
                n += 1
                invalid_article_org.append(orgtitle_noLF)
                #print(invalid_article)
                break


            # 获取引文文献的部分信息（标题，作者，摘要等）
            get_detail(output_url(lv))

            article_out = pandas.DataFrame(result_list["article_detail"])
        total += result_list["article_detail"]
    else:
        i = 0
        break_flag = False
        for i in range(0, 10):
            try:
                lv = bs4(CJFD_url).select('a[target="_blank"]')[i]
            except:
                n += 1
                invalid_article_org.append(orgtitle_noLF)
                break_flag = True
                #print(invalid_article)
                break

            # 获取引文文献的部分信息（标题，作者，摘要等）
            get_detail(output_url(lv))

            article_out = pandas.DataFrame(result_list["article_detail"])

        if break_flag == True:
            continue

        i = 0
        for i in range(0, num - 10):
            quote_final_url_page2 = 'http://www.cnki.net/kcms/detail/frame/list.aspx?dbcode=' + dbcode1 + '&filename=' + filename3 + '&dbname=' + dbname3 + \
                                    '&RefType=1&vl=' + value1 + '&CurDBCode=' + dbcode1 + '&page=2'

            try:
                lv = bs4(quote_final_url_page2).select('a[target="_blank"]')[i]
            except:
                n += 1
                invalid_article_org.append(orgtitle_noLF)
                #print(invalid_article)
                continue

            # 获取引文文献的部分信息（标题，作者，摘要等）
            get_detail(output_url(lv))

            article_out = pandas.DataFrame(result_list["article_detail"],columns=['orgtitle', 'title', 'author','orgn', 'ChDivSummary', 'catalog_FUND', 'catalog_KEYWORD',
             'catalog_ZCDOI','catalog_ZTCLS'])

        total += result_list["article_detail"]


    article_out = pandas.DataFrame(total,columns=['orgtitle', 'title', 'author','orgn', 'ChDivSummary', 'catalog_FUND', 'catalog_KEYWORD','catalog_ZCDOI','catalog_ZTCLS'])
    article_out.to_excel(part_article_out)

print('\n\n\n%d篇文章获取失败：'% (n),'\n',invalid_article_org,'\n',lost_quote_article,'\n\n\n\n\n\n\n##############现在对这些文章进行二次抓取##############\n\n\n\n\n\n\n' )
final_invalid_article = []









#对第一次抓取失败的文章做二次抓取
n = 0
x = 0

for i in invalid_article_org:

    lines = len(invalid_article)
    print(lines)

    result_list["article_detail"] = [0, ]

    x += 1

    orgtitle = i.replace('\n','')

    print('No%d:%s' % (x, i))

    # 生成以每篇文章作为关键字的检索页面,并产生第一篇文章的链接
    base_url = 'http://scholar.cnki.net/result.aspx?q=' + urllib.parse.quote(orgtitle) + '&rt=&rl=&udb='

    try:
        article = bs4(base_url).select('.gotodetaillink')[0]
    except (IndexError):
        n += 1
        final_invalid_article.append(orgtitle)
        #print(final_invalid_article)
        continue

    first_article_url = str(article_url.search(str(article)).group(1)).replace('&amp;', '&').replace('\r', '').replace('\n', '')

    # 从指定文章的源代码提取其引文的关键信息，并生成引文链接
    try:
        value = bs4(first_article_url).select('#listv')[0]
        value1 = quote_url.search(str(value)).group(1)
        dbcode1 = dbcode.search(str(first_article_url)).group(1)[:4]
        filename3 = filename2.search(str(first_article_url)).group(1)
        dbname3 = dbname2.search(str(first_article_url)).group(1)
    except:
        n += 1
        final_invalid_article.append(orgtitle)
        #print(final_invalid_article)
        continue

    quote_final_url = 'http://www.cnki.net/kcms/detail/frame/list.aspx?dbcode=' + dbcode1 + '&filename=' + filename3 + '&dbname=' + dbname3 + \
                      '&RefType=1&vl=' + value1
    #print(quote_final_url)




    #用于检测是否存在CJFD(中国学术期刊网络出版总库）
    try:
        CJFD = bs4(quote_final_url).select('.dbName')[0]
        #print(CJFD)
    except:
        n += 1
        final_invalid_article.append(orgtitle_noLF)
        #print(final_invalid_article)
        continue

    CJFD_exist = re.findall(r"中国期刊全文数据库", str(CJFD.text))

    if CJFD_exist:
        CJFD_url = quote_final_url + '&CurDBCode=CJFD'
        #print(CJFD_url)
        num = int(bs4(quote_final_url).select('.count')[0].text.replace(' ', '')[5: -3])
        #print(num)

        if num != 0:
            pass
        else:
            n += 1
            lost_quote_article.append(orgtitle)
            #print(final_invalid_article)
            continue
    else:
        n += 1
        lost_quote_article.append(orgtitle)
        continue



    # 获取引文的篇数
    # try:
    #     num = int(bs4(quote_final_url).select('.count')[0].text.replace(' ', '')[5: -3])
    # except:
    #     n += 1
    #     final_invalid_article.append(orgtitle)
    #     #print(final_invalid_article)
    #     continue

    result_list["article_detail"] = [
        dict(orgtitle='', title='', author='', orgn='', ChDivSummary='', catalog_FUND='', catalog_KEYWORD='',
             catalog_ZCDOI='', catalog_ZTCLS='')]


    if num >= 1 and num <= 10:
        i = 0
        for i in range(0, num):
            try:
                lv = bs4(CJFD_url).select('a[target="_blank"]')[i]
            except:
                n += 1
                final_invalid_article.append(orgtitle)
                #print(final_invalid_article)
                break

            # 获取引文文献的部分信息（标题，作者，摘要等）
            get_detail(output_url(lv))

            article_out = pandas.DataFrame(result_list["article_detail"])
        total += result_list["article_detail"]
    else:
        i = 0
        break_flag = False
        for i in range(0, 10):
            try:
                lv = bs4(CJFD_url).select('a[target="_blank"]')[i]
            except:
                n += 1
                final_invalid_article.append(orgtitle)
                #print(final_invalid_article)
                break_flag = True

                break

            # 获取引文文献的部分信息（标题，作者，摘要等）
            get_detail(output_url(lv))

            article_out = pandas.DataFrame(result_list["article_detail"])

        if break_flag == True:
            continue

        i = 0
        for i in range(0, num - 10):
            quote_final_url_page2 = 'http://www.cnki.net/kcms/detail/frame/list.aspx?dbcode=' + dbcode1 + '&filename=' + filename3 + '&dbname=' + dbname3 + \
                                    '&RefType=1&vl=' + value1 + '&CurDBCode=' + dbcode1 + '&page=2'

            try:
                lv = bs4(quote_final_url_page2).select('a[target="_blank"]')[i]
            except:
                n += 1
                final_invalid_article.append(orgtitle)
                #print(final_invalid_article)
                continue

            # 获取引文文献的部分信息（标题，作者，摘要等）
            get_detail(output_url(lv))

            article_out = pandas.DataFrame(result_list["article_detail"],columns=['orgtitle', 'title', 'author','orgn', 'ChDivSummary', 'catalog_FUND', 'catalog_KEYWORD',
             'catalog_ZCDOI','catalog_ZTCLS'])

        total += result_list["article_detail"]


    article_out = pandas.DataFrame(total,columns=['orgtitle', 'title', 'author','orgn', 'ChDivSummary', 'catalog_FUND', 'catalog_KEYWORD','catalog_ZCDOI','catalog_ZTCLS'])
    article_out.to_excel(final_article_out)

print("\n\n###########%s篇文章已获取，%s篇文章未获取成功，成功率为%.2f%%###########" % (m - n, n,((m-n)*100/(m))))
print('\n\n\n下列文章缺失引文：',lost_quote_article)
print('\n\n\n其他原因未获取的文章:', final_invalid_article)
