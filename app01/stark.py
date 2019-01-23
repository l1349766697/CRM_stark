



print("app01>>>>>")

from stark.service.sites import site,ModelStark
from . import models


class BookConfig(ModelStark):

    def show_authors(self,obj=None,is_header=False): # 需要自定义这个方法，在显示的时候用方法来调用，表头和表体显示不一样
        if is_header:
            return "作者"

        return " ".join([obj.name for obj in obj.authors.all()])

    list_display = ["title","price","publish","pub_date",show_authors] # 这里直接publish拿到的是该表的一个object对象
    list_display_links = ["title","price"]
    search_fields=["title"]

    # 批量初识化
    def patch_init(self,request,queryset):  # 定义方法
        queryset.update(price=100)

    patch_init.short_desc = "批量初始化"  # 起名
    actions = [patch_init,]  # 添加进actions列表展示

    list_filter = ["publish","authors"]

class AuthorConfig(ModelStark):
    # def show_gender(self,obj=None,is_header=False):
    #     if is_header:
    #         return "性别"
    #     return obj.get_gender_display()  # 记录对象点这个方法，gender是字段名，就可以拿到字段的映射值

    list_display = ["name","age",'gender']
    list_filter = ("gender",)


site.register(models.Book,BookConfig)
site.register(models.Publish)
site.register(models.Author,AuthorConfig)
site.register(models.AuthorDetail)
















