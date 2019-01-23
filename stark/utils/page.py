class Pagination(object):

    def __init__(self,current_page,all_count,request,per_page=10,max_pager_num=11):
        '''
        封装分页相关数据：
        :param current_page:   当前页
        :param all_count:      数据库中的数据总条数
        :param per_page:       每页显示的数据条数
        :param max_pager_num:  最多显示的页码个数
        :param num_pages:      计算总页数
        '''

        try:
            current_page = int(current_page)
        except Exception as e:
            current_page = 1

        if current_page < 1:  # 输入的页数如果小于1，也直接返回首页给用户
            current_page = 1

        self.current_page = current_page
        self.all_count = all_count
        self.per_page = per_page

        # 计算总页数
        num_pages, tmp = divmod(all_count, per_page) # 得到总页数和是否有余数，余数为最后一页的显示
        if tmp:
            num_pages += 1
        self.num_pages = num_pages

        self.max_pager_num = max_pager_num  # 最大显示页码数
        # 5 显示左右各显示一半的页码
        self.pager_count_half = int((self.max_pager_num -1) / 2)

        # 请求信息字典，通过这个来完成保存分页器的搜索条件
        import copy
        self.params = copy.deepcopy(request.GET)  # 拿到queryset类型的类字典结果

    '''     
       self.num_pages=100
       per_page=8


       current_page =1     [0:8]
       current_page =2     [8:16]
       current_page =3     [16:24]
                           [(current_page-1)*per_page:current_page*per_page ]

       '''
    # 通过你当前的页码，拿到你要显示的一开始的数据，到最后一条显示,显示该范围的数据
    @property
    def start(self):
        return (self.current_page - 1) * self.per_page

    # 通过你当前的页码，拿到你要显示的最后一条数据，
    @property
    def end(self):
        return self.current_page * self.per_page

    # 对点击的页码不同情况，展示不一样的效果，总页码小于最多显示页码数，直接全部显示，
    # 获取页码，返回显示页码的效果给前端，模板文件通过调用，得到返回值，把返回值放到前端，渲染出来
    def page_html(self):

        # 如果总页码 < 11个：小于最多可以显示的页码个数，直接全部显示
        if self.num_pages <= self.max_pager_num:
            pager_start = 1
            pager_end = self.num_pages + 1  # 注意这里是根据总页数加一
        # 总页码  > 11，大于最多可以显示的页码个数
        else:
            # 头显示：当前页如果 <= 页面上最多显示11/2 个一半的页面，就显示从1到最多的显示页码数
            if self.current_page <= self.pager_count_half:
                pager_start = 1
                pager_end = self.max_pager_num + 1

            # 尾显示：点击的页码，加上末尾的页码超过了计算总页码数，显示从最后一个页码往回算，显示最多的页码数
            elif (self.current_page + self.pager_count_half) > self.num_pages:
                pager_start = self.num_pages - self.max_pager_num + 1 # 末尾的显示页码数，当加一半的最大显示页码数时超过了总页码数，就默认显示最后的最多页码数
                pager_end = self.num_pages + 1  # 保证前开后闭，的后闭也能取到，所以要加1

            # 中间的页码显示，当前页码居中，左右各一半
            else:
                pager_start = self.current_page - self.pager_count_half
                pager_end = self.current_page + self.pager_count_half + 1  # 保证后闭也能取到，所以加1


        # 传给前端显示的页码列表
        page_html_list = []

        # 首页 上一页标签
        self.params["page"] = 1  # 改变page的页码，其他搜索条件不改变
        first_page = '<nav aria-label="Page navigation"><ul class="pagination"><li><a href="?%s">首页</a></li>' % (self.params.urlencode(),)
        page_html_list.append(first_page)

        # 对上一页标签的处理
        if self.current_page <= 1:  # 如果当前页码数减1,小于1,就不让点击上一页按钮
            prev_page = '<li class="disabled"><a href="#">上一页</a></li>'
        else:
            self.params['page'] = self.current_page - 1
            prev_page = '<li><a href="?%s">上一页</a></li>' % (self.params.urlencode(),) # 返回urlencode格式的数据，publish=1
        page_html_list.append(prev_page)


        # 显示每一页的最大页码数（变动的显示最多页码的范围）
        for i in range(pager_start,pager_end):
            self.params["page"] = i
            if i == self.current_page: # 如果是当前页码，就显示不同的颜色
                temp = '<li class="active"><a href="?%s">%s</a></li>' % (self.params.urlencode(), i,)
            else:
                temp = '<li><a href="?%s">%s</a></li>' % (self.params.urlencode(), i,)
            page_html_list.append(temp)

        # 下一页
        self.params["page"] = self.current_page + 1
        if self.current_page >= self.num_pages: # 下一页页码超过总页码，限制下一页点击功能
            next_page = '<li class="disabled"><a href="#">下一页</a></li>'
        else:
            next_page = '<li><a href="?%s">下一页</a></li>' % (self.params.urlencode())
        page_html_list.append(next_page)

        # 尾页
        self.params["page"] = self.num_pages  # 改变page的页数，保存其他搜索条件
        last_page = '<li><a href="?%s">尾页</a></li></ul></nav>' % (self.params.urlencode())
        page_html_list.append(last_page)

        return "".join(page_html_list)
















