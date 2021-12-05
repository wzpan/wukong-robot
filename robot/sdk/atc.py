# # -*- coding=utf-8 -*-
# digit=['零','一','二','三','四','五','六','七','八','九']
# unit=['零','十','百','千','万','亿']
# def arabic_to_chinese(number):
# 	if number < 0:
# 		raise Exception("negative arg")
# 	if number < 10:
# 		return digit[number]
# 	elif number < 100:
# 		h = number // 10
# 		if h != 1:
# 			return str(h) + "十" + arabic_to_chinese(number % 10)
# 		else:
# 			return "十" + arabic_to_chinese(number % 10)
# 	elif number < 1000:
# 		th = number // 100
# 		return str(th) + "百" + arabic_to_chinese(number % 100)
# 	elif number < 10000:
# 		w = number // 1000
# 		return str(w) + "千" + arabic_to_chinese(number % 1000)
# 	else:
# 		pass


# c = 1
# def test(num, expected):
# 	global c
# 	actual = arabic_to_chinese(num)
# 	if (actual != expected):
# 		print(c, actual, expected)
# 	else:
# 		print(c, "pass")
# 	c+=1


# test(0, '零')
# test(1, '一')
# test(5, '五')
# test(12, '十二')
# test(30, '三十')
# test(37, '三十七')
# test(100, '一百')
# test(150,'一百五十')
# test(156,'一百五十六')
# test(999,'九百九十九')
# test(1000 ,'一千')
# test(1001 ,'一千零一')
# test(1001 ,'一千零一')

# -*- coding: utf-8 -*-

# Licensed under WTFPL or the Unlicense or CC0.
# This uses Python 3, but it's easy to port to Python 2 by changing
# strings to u'xx'.

import itertools


def num2chinese(num, big=False, simp=True, o=False, twoalt=False):
    """
    Converts numbers to Chinese representations.
    `big`   : use financial characters.
    `simp`  : use simplified characters instead of traditional characters.
    `o`     : use 〇 for zero.
    `twoalt`: use 两/兩 for two when appropriate.
    Note that `o` and `twoalt` is ignored when `big` is used, 
    and `twoalt` is ignored when `o` is used for formal representations.
    """
    # check num first
    nd = str(num)
    if abs(float(nd)) >= 1e48:
        raise ValueError("number out of range")
    elif "e" in nd:
        raise ValueError("scientific notation is not supported")
    c_symbol = "正负点" if simp else "正負點"
    if o:  # formal
        twoalt = False
    if big:
        c_basic = "零壹贰叁肆伍陆柒捌玖" if simp else "零壹貳參肆伍陸柒捌玖"
        c_unit1 = "拾佰仟"
        c_twoalt = "贰" if simp else "貳"
    else:
        c_basic = "〇一二三四五六七八九" if o else "零一二三四五六七八九"
        c_unit1 = "十百千"
        if twoalt:
            c_twoalt = "两" if simp else "兩"
        else:
            c_twoalt = "二"
    c_unit2 = "万亿兆京垓秭穰沟涧正载" if simp else "萬億兆京垓秭穰溝澗正載"
    revuniq = lambda l: "".join(k for k, g in itertools.groupby(reversed(l)))
    nd = str(num)
    result = []
    if nd[0] == "+":
        result.append(c_symbol[0])
    elif nd[0] == "-":
        result.append(c_symbol[1])
    if "." in nd:
        integer, remainder = nd.lstrip("+-").split(".")
    else:
        integer, remainder = nd.lstrip("+-"), None
    if int(integer):
        splitted = [integer[max(i - 4, 0) : i] for i in range(len(integer), 0, -4)]
        intresult = []
        for nu, unit in enumerate(splitted):
            # special cases
            if int(unit) == 0:  # 0000
                intresult.append(c_basic[0])
                continue
            elif nu > 0 and int(unit) == 2:  # 0002
                intresult.append(c_twoalt + c_unit2[nu - 1])
                continue
            ulist = []
            unit = unit.zfill(4)
            for nc, ch in enumerate(reversed(unit)):
                if ch == "0":
                    if ulist:  # ???0
                        ulist.append(c_basic[0])
                elif nc == 0:
                    ulist.append(c_basic[int(ch)])
                elif nc == 1 and ch == "1" and unit[1] == "0":
                    # special case for tens
                    # edit the 'elif' if you don't like
                    # 十四, 三千零十四, 三千三百一十四
                    ulist.append(c_unit1[0])
                elif nc > 1 and ch == "2":
                    ulist.append(c_twoalt + c_unit1[nc - 1])
                else:
                    ulist.append(c_basic[int(ch)] + c_unit1[nc - 1])
            ustr = revuniq(ulist)
            if nu == 0:
                intresult.append(ustr)
            else:
                intresult.append(ustr + c_unit2[nu - 1])
        result.append(revuniq(intresult).strip(c_basic[0]))
    else:
        result.append(c_basic[0])
    if remainder:
        result.append(c_symbol[2])
        result.append("".join(c_basic[int(ch)] for ch in remainder))
    return "".join(result)
