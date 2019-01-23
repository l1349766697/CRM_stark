
from django.shortcuts import HttpResponse,render,redirect

from django.urls import path,re_path

from django.core.exceptions import FieldDoesNotExist # 引入这个错误类型
from app01.models import *
from django.utils.safestring import mark_safe # 告诉前端不要把我这个写的标签转义，直接渲染我写的这个标签
from django.urls import reverse  # 用来反向解析的
from django import forms  # 用来使用modelform组件的
from stark.utils.page import Pagination  # 引入分页器
import copy
from django.db.models.fields.related import ForeignKey,ManyToManyField
from django.db.models import Q


class ShowList():   # 展示类，装饰配置类的；用来跟前端对接，显示传递要展示的样式给前端

    def __init__(self,config_obj,request,queryset):
        self.config_obj = config_obj  # 这里需要传的是配置类对象
        self.request = request  # 传request，分页器那里需要使用到
        self.queryset = queryset  # 所有表数据的queryset集合对象
        self.getPagination()  # 默认执行调用分页器，实例化出分页器对象

    # 获取搜索的查询的条件，通过Q对象来组合成条件
    def get_search_condition(self):
        val = self.request.GET.get("q")  #  拿到该键值对的值
        search_condition = Q()  # 实例化一个Q对象，没有查询条件返回一个空的Q对象，就可以不进行查询，如果返回None在进行filter过滤时会报错
        if val:
            self.search_default_val = val
            # print("search_fields",self.config_obj.search_fields) # ['title', 'price']
            search_condition.connector = "or"  # 定义or的条件为搜索条件，默认是and组合查询条件
            for search_field in self.config_obj.search_fields:
                search_condition.children.append((search_field + "__icontains", val))  # 这里可以将str转换变量，将搜索条件添加进实例对象中，可以对搜索条件进行搜索
        print("ser?????????",search_condition)
        return search_condition  # 返回搜索结果


    # 多级过滤，通过Q对象实现
    def get_filter_condition(self):
        filter_condition = Q()  # 实例化Q对象,默认and组合查询
        for key,val in self.request.GET.items():  # authors=1&publish=1  # 拿到字典，循环拿到所有的键值对
            if key in ["page","q"]:  # 点分页时，发送page=2,这样的键值对，去过滤，没有这样的字段，所有直接跳过他，这是分页器的事情，不要在这里被拦下来了，直接continue
                continue
            filter_condition.children.append((key,val))  # 需要传一个元组 # filter查询支持这种查法，Book.objects.filter(authors=1)这种正好跟authors=1&publish=1符合, 其他两种 authors__id=1, authors=对象
        return filter_condition


    # 实例化一个分页器对象
    def getPagination(self):
        current_page = self.request.GET.get('page')  # 拿到当前页码数
        # 这里需要进行三步，拿到所有的数据，进行search过滤，然后在进行filter过滤，经过分页，最后才显示出来
        search_condition = self.get_search_condition()  # 拿到搜索的条件

        filter_conditon = self.get_filter_condition() # 拿到过滤的条件
        print("search_condition>>>>>>>>", filter_conditon)
        # 先按搜索的条件过滤，再按过滤的条件，
        filter_queryset = self.queryset.filter(search_condition)
        print("<<<<<<<<<<<<<<<<<<<<<<<<<")
        filter_queryset = filter_queryset.filter(filter_conditon)
        self.pagination = Pagination(current_page,filter_queryset.count(),self.request,per_page=8)  # 实例化分页器对象
        self.pager_queryset = filter_queryset[self.pagination.start:self.pagination.end]  # 通过对所有数据切片出，然后分页显示出来


    def show_header(self):
        # header_list=["名称","价格","出版日期","出版社"]
        # 展示当前表头数据  header_list=["名称","价格","出版日期","出版社"]
        header_list = []
        for field in self.config_obj.get_new_list_display():
            try:
                field_obj = self.config_obj.model._meta.get_field(field)  # 拿到该字段的对象
                header_list.append(field_obj.verbose_name)  # verbose.name是字段对象的一个属性，默认是字段名，可以在模型类设置等于中文
            except FieldDoesNotExist as e:
                if field == "__str__":  # 特例，不传参，使用父类的默认值"__str__"，如：publish表这时拿到的是__str__字符串
                    val = self.config_obj.model._meta.model_name.upper()
                else:
                    val = field(self.config_obj, is_header=True)  # 调用子类的函数，因为是类名直接调用所以此时是方法，需要传self参数
                header_list.append(val)
        return header_list


    def show_body(self):

        # 展示当前表体数据
        data = []  # 最终传给模板文件的样式：[["西游记",price],[title,price],]
        queryset = self.config_obj.model.objects.all()  # 拿到一个queryset的集合对象，元素为每一本书或每一个模型类的对象(表的数据每一条记录)
        # print(queryset)
        print("list_display >>>", self.config_obj.list_display)  # ['title', 'price']

        for obj in self.pager_queryset:  # 这里是要展示经过分页器对象，之后的表记录对象，不再是显示所有了
            temp = []
            a = self.config_obj.get_new_list_display()
            print(a)
            for field in self.config_obj.get_new_list_display():

                if callable(field):  # 多对多字段会调用函数（类名调用方法即调用函数）
                    val = field(self.config_obj, obj)  # 执行函数要传参数self，
                else:                                                # 如果是__str__它会去执行，拿到返回值
                    try:
                        field_obj = self.config_obj.model._meta.get_field(field) # 拿到字段对象
                        if field_obj.choices:  # 如果该字段是chooices
                            val = getattr(obj,"get_"+field+"_display")  # 记录对象点这个方法，拿到该字段的映射值
                        else:
                            val = getattr(obj, field)  # 记录对象点拿到字段的值
                    except FileNotFoundError as e:
                        val = getattr(obj,field)() # 通过__str__拿到是一个方法（函数体），所以要加括号来执行，拿到返回值，这里比较特殊，因为拿到的函数体，不加括号，render渲染的时候也会被执行，也可以拿到返回值，一般不这样做，原理不一样

                    if field in self.config_obj.list_display_links:  # 判断如果是用户自定义的编辑字段，就将该字段变成a标签，跳转到编辑页面，
                        val = "<a href='%s'>%s</a>" % (self.config_obj.get_edit_url(obj), val)  # 重新赋值，将其变成a标签，并显示字段内容
                temp.append(mark_safe(val))  # 要用mark_safe命令告诉前端不要转义这个标签命令，渲染出编辑的a标签字段
            data.append(temp)
        return data

    '''
    data=[
     ["python",122,"alex egon"],
     ["linux",234,"alex"],
     ["go",34,"alex egon"],   
    ]

    '''

    # 展示批量操作
    def show_actions(self):
        actions_list = []
        for action in self.config_obj.get_new_actions():
            actions_list.append({
                "name":action.__name__,  # 拿到批量操作的方法名，注意模板中绝对不能使用这种双下划线的方法
                "desc":action.short_desc, # 拿到批量操作方法的名字
            })
        return actions_list

    # 展示多级过滤标签
    def show_list_filter(self):
        links_dict = {}
        # 你点击的时候就会发送一下，
        for field in self.config_obj.list_filter:  #  ["publish","authors"] 要过滤的字段对象

            params = copy.deepcopy(self.request.GET) # 不能放在循环外面，复制一份请求的数据，里面是字典来的, 放在循环里面保证，原来的数据不被修改，而只改变你要修改的
            field_obj = self.config_obj.model._meta.get_field(field)  # 将字符串的字段名，拿到字段对象

            # print(field_obj,type(field_obj))
            from django.db.models.fields.related import ForeignKey
            # print("remote_field",field_obj.remote_field.model)

            if isinstance(field_obj,ForeignKey) or isinstance(field_obj,ManyToManyField): # 处理外键字段和多对多字段
                rel_model = field_obj.remote_field.model  # 通过字段对象，拿到该字段对应的关联的表
                # data_list :queryset：关联表数据
                data_list = rel_model.objects.all() # 拿到关联表的所有queryset对象
            elif field_obj.choices:
                data_list = field_obj.choices  # ((1,"男"),(2,"女"))
            else:
                data_list = []  # 处理普通字段，过滤一般不用普通字段，可以直接给抛错


            links = []
            # all就是删除当前循环的过滤条件，留下其他的过滤条件
            if params.get(field):
                params.pop(field)  # 删除当前字段对象的标签，保留其他字段对象的标签
            link_all = "<a class='btn btn-default btn-sm' href='?%s'>All</a>" % params.urlencode()
            links.append(link_all)

            for data in data_list:  # 循环queryset集合，拿到每一条字段的数据类型，根据数据类型进行不同逻辑处理，显示成a标签
                if type(data) == tuple: # data_list= ((1,"男"),(2,"女"))
                    pk, text = data
                else:                   # data_list= queryset
                    pk, text = data.pk, str(data)  # 拿到模型类对象

                current_field_val = self.request.GET.get(field) # publish=1，拿到当前点击的主键值
                params[field] = pk  #******* 这里存放a标签的href的路径，已存在的修改，没有的就新增，通过urlencode变成publish=1&authors=1的请求体格式
                if str(pk) == current_field_val:  # 值一样，说明是当前点击的，显示颜色加深
                    link = "<a class='active btn btn-default btn-sm' href='?%s'>%s</a>"%(params.urlencode(),text)
                else:
                    link = "<a class='btn btn-default btn-sm' href='?%s'>%s</a>" %(params.urlencode(),text)
                links.append(link)  # 添加关联的字段的表的每一个字段对象进一个列表
            links_dict[field] = links  # 每一个过滤字段为一键值对
        return links_dict





class ModelStark():  # 配置类

    list_display = ["__str__"] # 用户没有定义该显示列表，默认执行模型类的__str__，显示表对象
    list_display_links = [] # 让用户可以自定义点击编辑的字段，没有自定义显示默认的编辑按钮
    model_form_class = None  # 提供用户的自定义modelform接口，
    search_fields = []  # 提供用户搜索框的功能，默认不显示，用户有自定义才显示
    list_filter = [] #


    def __init__(self,model):
        self.model = model

        # 配置反向解析的元组即元组里面放APP的名称和表名：(label_name,model_name)
        self.model_name = self.model._meta.model_name # 取到当前模型类的名字（即表名）
        self.app_label = self.model._meta.app_label  # 取到该模型类所在APP名字
        self.app_model = (self.app_label, self.model_name)

    # 批量删除， 批量操作三步走，一定义方法，二给该方法起中文名，三加到action里面去
    def patch_delete(self,request,queryset):
        queryset.delete()  #  删除选中的字段对象
        # return HttpResponse("删除成功")  # 一般没有返回值

    patch_delete.short_desc = "批量删除"  # 为批量删除定义一个名字，一切皆对象，相当于对这个方法定义了一个类属性

    actions = []  # 提供用户批量操作的接口，默认带上批量删除的功能

    # 让所有的表格都默认带上批量删除的方法
    def get_new_actions(self):
        temp = []
        temp.extend(self.actions)  # 用新的列表接收actions，添加默认的，返回新的actions列表
        temp.insert(0, self.patch_delete)
        return temp

    # 选择，删除，编辑 列
    def _checkbox(self, obj=None, is_header=False):
        if is_header:
            return "选择"
        return mark_safe("<input type='checkbox' name='choose_pk' value='%s'>" % obj.pk) # 注意引号啊，要细心

    def _edit(self,obj=None,is_header=False): # obj是当前表记录的对象
        if is_header:
            return "编辑"
        # app_label = obj._meta.app_label
        # model_name = obj._meta.model_name  # 这里先暂时写成这个动态url，后面我们使用url反向解析来解决这个问题
        return mark_safe("<a href='%s'>编辑</a>" % self.get_edit_url(obj))

    def _delete(self,obj=None,is_header=False): # obj是当前表记录的对象
        if is_header:
            return "删除"
        return mark_safe("<a href='%s'>删除</a>" % self.get_delete_url(obj))

    # 让所有的查看页面都默认带上这三列选项，选择，删除，编辑
    def get_new_list_display(self):
        new_list_display=[]
        new_list_display.extend(self.list_display) # 将当前的要显示的列表遍历添加到这个新列表中
        new_list_display.insert(0,ModelStark._checkbox) # 在第一个位置插入选择列
        if not self.list_display_links: # 判断用户有自定义编辑的字段，就不显示默认的编辑按钮了
            new_list_display.append(ModelStark._edit)  #
        new_list_display.append(ModelStark._delete) # 默认添加的 删除功能列的按钮
        return new_list_display


    def list_view(self,request):
        # self  ;        模型类对应的配置类对象,可能是自定义配置类对象,也可能是默认配置类ModelStark对象
        # self.model:    当前访问表的模型类

        if request.method == "POST":  # actions处理
            patch_func_str = request.POST.get("patch_func") # 拿到选择要执行的批量操作的方法的名字（注意这里拿到的其字符串类型的名字）
            choose_pk = request.POST.getlist("choose_pk")  # 拿到要进行操作的列表，找到要操作的字段对象
            queryset = self.model.objects.filter(pk__in=choose_pk)  # 通过主键在选择的主键列表中，筛选出要进行批量操作的字段对象
            # print(patch_func_str, choose_pk)  # patch_delete ['4', '6']
            patch_func = getattr(self,patch_func_str) # 通过反射拿到，该方法的变量名
            res = patch_func(request,queryset)  # 执行该批量操作方法
            if res:  # 判断是否有返回值，用户有自定义返回值，直接返回，没有默认返回查看显示页面
                return res

        queryset = self.model.objects.all()  # Book.objects.all()  # 拿到所有表格的记录对象（queryset对象）
        show_list = ShowList(self,request,queryset)  # 展示类实例化一个对象，将当前的配置类对象，用self传参进去

        # 为添加按钮获取模型变量信息
        table_name = self.model._meta.verbose_name  # 获取表名
        add_url = self.get_add_url() # 获取当前添加的路径

        return render(request, "stark/list_view.html", locals())


    # 设置默认的modelform，用于校验数据、获取、传递；并在此提供接口，可以让用户自定modelform
    def get_model_form_class(self):
        class BaseModelForm(forms.ModelForm):
            class Meta:
                model = self.model # 得到动态数据表对象
                fields = "__all__"  # 显示所有的字段

        return self.model_form_class or BaseModelForm #用户有自定义，用用户的，没有用默认的


    def add_view(self,request):
        # self  ;        模型类对应的配置类对象,可能是自定义配置类对象,也可能是默认配置类ModelStark对象
        # self.model:    当前访问表的模型类

        # 通过ModelForm来进行编辑添加功能，实例化一个modelform对象，
        DetailModelForm = self.get_model_form_class()
        if request.method == "POST":  # 注意这里请求方式要大写
            form = DetailModelForm(request.POST) # 拿到post请求体的数据
            if form.is_valid():  # 该命令就是进行校验
                form.save() # 这个命令就是添加，若实例化的时候有instance就是编辑更新
                return redirect(self.get_list_url()) # 添加成功，重定向到查看页面
            else:
                return render(request,"stark/add_view.html",{"form":form}) # 校验不通过，返回原添加页面，并提示错误信息
        else:
            form = DetailModelForm()
            return render(request,"stark/add_view.html",{"form":form})


    def change_view(self,request,id):
        # self  ;        模型类对应的配置类对象,可能是自定义配置类对象,也可能是默认配置类ModelStark对象
        # self.model:    当前访问表的模型类
        DetailModelForm = self.get_model_form_class()
        edit_obj=self.model.objects.filter(pk=id).first()
        if request.method == "GET":

            form = DetailModelForm(instance=edit_obj)
            return render(request, "stark/change_view.html", {"form": form})
        else:
            form = DetailModelForm(request.POST,instance=edit_obj)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            else:
                return render(request, "stark/change_view.html", {"form": form})





        # return HttpResponse("change_view")


    def delete_view(self,request,id):
        # self  ;        模型类对应的配置类对象,可能是自定义配置类对象,也可能是默认配置类ModelStark对象
        # self.model:    当前访问表的模型类

        list_url = self.get_list_url()
        if request.method == "POST":
            self.model.objects.filter(pk=id).delete()
            return redirect(list_url)
        return render(request,"stark/delete_view.html",locals())


    # 反向解析url，执行这里的方法可以动态的获取url路径
    # 通过别名找到对应的url，然后args会将数字传参给该url形成路径，然后执行相应的视图函数
    def get_list_url(self):
        _url = reverse("%s_%s_list" % self.app_model) # 通过别名反向解析出来的路径：/stark/app01/book/add
        return _url
    def get_add_url(self):
        _url = reverse("%s_%s_add" % self.app_model) # /stark/app01/book/
        return _url
    def get_edit_url(self, obj):
        _url = reverse("%s_%s_change" % self.app_model, args=(obj.pk,))  # /stark/app01/book/2/change/
        return _url
    def get_delete_url(self, obj):
        _url = reverse("%s_%s_delete" % self.app_model, args=(obj.pk,)) # args传参给反向解析出来的url路径，
        return _url

    # urls二级分发， 使用反向解析来做url
    def get_urls(self):
        temp = [
            path('',self.list_view,name="%s_%s_list" % self.app_model ), # 设置别名做反向解析，其他地方，根据这个别名就能找到这个路径
            path('add/',self.add_view,name="%s_%s_add" % self.app_model),
            re_path('(\d+)/change/',self.change_view,name="%s_%s_change" % self.app_model),
            re_path('(\d+)/delete/',self.delete_view,name="%s_%s_delete" % self.app_model),
        ]
        return temp

    # 将一个方法变成一个属性
    @property
    def urls(self):
        return self.get_urls(), None, None









class StarkSite():
    '''
    # StarkSite: 基本类----这里设置一级分发
    # model： 注册模型类
    # ModelStark： 注册模型类的配置类---这里设置二级分发，并设置别名用于反向解析
    '''

    def __init__(self):  # 定义这个字典在url二级分发时体现出来作用，
        self._registry = {} # model_class class -> admin_class instance

    def register(self,model,stark_class=None): # 传参，注册模型类和对应的配置类，这里传的都是类名，所以在调用方法的时候，实际上是调用函数，所以要传self
        stark_class = stark_class or ModelStark  # 若自定制有子类配置类对象则用传入的子类的，没有用默认父类的
        self._registry[model] = stark_class(model) #  该模型类为键，该模型了的配置类为值


    def get_urls(self):
        temp = []
        for model, config_obj in self._registry.items():  # {Book:Bookconfig(Book),Publish:ModelStark(Publish)}
            model_name = model._meta.model_name  # 拿到该表的小写表名
            app_label = model._meta.app_label  # 拿到该表所在的APP名称
            temp.append(
                path('%s/%s/' % (app_label, model_name),config_obj.urls) # 对象直接点该属性，这是一个方法封装的属性
            )
            '''
            # 1 path('app01/book/',Bookconfig(Book).urls),

            path('app01/book/', Bookconfig(Book).list_view),
            path('app01/book/add', Bookconfig(Book).add_view),
            path('app01/book/(\d+)/change/', Bookconfig(Book).change_view),
            path('app01/book/(\d+)/delete/', Bookconfig(Book).delete_view),
            '''

        return temp

    @property
    def urls(self):
        return self.get_urls(), None, None


site=StarkSite()












































