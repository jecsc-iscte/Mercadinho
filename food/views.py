from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from food.models import Mensagem, Customer, Salesman
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from .models import Product, Comment, CestoCompras
from .decorators import unauthenticated_user, allowed_users
from django.contrib.auth.models import User, Group
import random
import datetime

def redirect_view(request):
    return redirect('food:index')

def index(request):
    if request.user.groups.filter(name='Salesman').exists():
        products = Product.objects.filter(salesman_id=request.user.salesman.id)
    else:
        products = Product.objects.all()
    context = {'products_list': products}
    return render(request, 'food/index.html', context)


def contactos(request):
    if request.method == 'POST':
        Mensagem(email=request.POST.get("email"),
                 texto_mensagem=request.POST.get("message"),
                 dataHora=datetime.datetime.now(), tratada=False).save()
        return HttpResponseRedirect(reverse('food:contactos'))
    return render(request, 'food/contactos.html')


@login_required(login_url="food:loginutilizador")
def caixaMensagens(request):
    if request.method == "POST":
        filtro = request.POST.get('filtro')
        if filtro:
            lista_mensagens = Mensagem.objects.order_by('-dataHora').filter(tratada=filtro)
        else:
            lista_mensagens = Mensagem.objects.order_by('-dataHora').filter(tratada=False)
    else:
        lista_mensagens = Mensagem.objects.order_by('-dataHora').filter(tratada=False)
    return render(request, 'food/caixaMensagens.html', {'lista_mensagens': lista_mensagens})


@login_required(login_url="food:loginutilizador")
def tratarMensagem(request, mensagem_id):
    mensagem = Mensagem.objects.get(id=mensagem_id)
    mensagem.tratada = True
    mensagem.save()
    return HttpResponseRedirect(reverse('food:caixamensagens'))


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def cestoCompras(request):
    customer = Customer.objects.get(user=request.user)
    cesto_compras = CestoCompras.objects.filter(customer=customer)
    if cesto_compras:
        return render(request, 'food/cestoCompras.html', {'cesto_compras': cesto_compras, 'error_message': False})
    else:
        return render(request, 'food/cestoCompras.html', {'error_message': True})


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def addToCart(request, product_id):
    quant = request.POST.get('quant')
    if quant is None:
        customer = Customer.objects.get(user=request.user)
        product = Product.objects.get(id=product_id)
        shoppingCart = CestoCompras(customer=customer, product=product)
        shoppingCart.save()
        products_list = Product.objects.all()
        context = {'products_list': products_list, 'confirmation': 'Produto adicionado', 'p': product}
        return render(request, 'food/index.html', context)
    else:
        for x in range(int(quant)):
            user = request.user
            customer = Customer.objects.get(user=user)
            product = Product.objects.get(id=product_id)
            shoppingCart = CestoCompras(customer=customer, product=product)
            shoppingCart.save()
            Comment.objects.all().filter(product_id=product_id)
            product.addView()
        return HttpResponseRedirect(reverse('food:productDetailPage', args=(product_id,)))


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def removeFromCart(request, cestoCompras_id):
    get_object_or_404(CestoCompras, pk=cestoCompras_id).delete()
    return HttpResponseRedirect(reverse('food:cestocompras'))


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def limparCesto(request):
    customer = Customer.objects.get(user=request.user)
    CestoCompras.objects.filter(customer=customer).delete()
    return HttpResponseRedirect(reverse('food:cestocompras'))


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer', 'Salesman'])
def perfil(request):
    user = request.user
    if user.groups.filter(name='Customer'):
        profile_pic = user.customer.profile_pic
        infoTecnica = {"Username": user.username, "Tipo Cliente": "Cliente", "Créditos": user.customer.credit}
        infoPessoal = {"Email": user.email, "Género": user.customer.gender, "Aniversário": user.customer.birthday}
    else:
        profile_pic = user.salesman.profile_pic
        infoTecnica = {"Username": user.username, "Rating": user.salesman.rating, "Tipo Utilizador": "Vendedor"}
        infoPessoal = {"Email": user.email, "Telefone": user.salesman.phone_number}
    return render(request, "food/perfil.html",
                  {"profile_pic": profile_pic, 'infoTecnica': infoTecnica, 'infoPessoal': infoPessoal})


@unauthenticated_user
def registarCustomer(request):
    if request.method == "POST" and request.FILES['photo']:
        image = request.FILES['photo']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        uploaded_file_url = fs.url(filename)
        if not User.objects.filter(username=request.POST["username"]):
            user = User.objects.create_user(
                username=request.POST["username"],
                password=request.POST["password"],
                email=request.POST["email"]
            )
            Group.objects.get(name='Customer').user_set.add(user)
            Customer(
                profile_pic=uploaded_file_url,
                gender=request.POST["gender"],
                birthday=request.POST["birthday"],
                credit=request.POST["credits"],
                user=user
            ).save()
            login(request, user)
            return HttpResponseRedirect(reverse('food:index'))
        else:
            return render(request, 'food/registarCustomer.html', {'error_message': 'Utilizador já criado com esse username'})
    return render(request, 'food/registarCustomer.html')


@unauthenticated_user
def registarSalesman(request):
    if request.method == "POST" and request.FILES['photo']:
        image = request.FILES['photo']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        uploaded_file_url = fs.url(filename)
        if not User.objects.filter(username=request.POST["username"]):
            user = User.objects.create_user(
                username=request.POST["username"],
                password=request.POST["password"],
                email=request.POST["email"]
            )
            Group.objects.get(name='Salesman').user_set.add(user)
            Salesman(
                profile_pic=uploaded_file_url,
                rating=0,
                phone_number=request.POST["telephone"],
                user=user
            ).save()
            login(request, user)
            return HttpResponseRedirect(reverse('food:index'))
        else:
            return render(request, 'food/registarSalesman.html',
                          {'error_message': 'Utilizador já criado com esse username'})
    return render(request, 'food/registarSalesman.html')


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Salesman'])
def addProduct(request):
    if request.method == 'POST' and request.FILES['myfile']:
        productImage = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(productImage.name, productImage)
        uploaded_file_url = fs.url(filename)
        salesman = Salesman(user=request.user)
        Product.objects.create(name=request.POST.get('productName'),
                               description=request.POST.get('productDescription'),
                               price=float(request.POST.get('productPrice')),
                               image=uploaded_file_url,
                               salesman=salesman
                               )
        return HttpResponseRedirect(reverse('food:index'))
    return render(request, 'food/add_product.html')


@unauthenticated_user
def loginutilizador(request):
    if request.method == "POST":
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
        except KeyError:
            return render(request, 'food/loginutilizador.html')
        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('food:index'))
            else:
                return render(request, 'food/loginutilizador.html',
                              {'error_message': 'Utilizador não existe ou a password está incorreta'})
        else:
            return render(request, 'food/loginutilizador.html')
    else:
        return render(request, 'food/loginutilizador.html')


@login_required(login_url="food:loginutilizador")
def logoututilizador(request):
    logout(request)
    return HttpResponseRedirect(reverse('food:index'))


def mapPage(request):
    return render(request, 'food/mercadinhos_map.html')


def aboutPage(request):
    return render(request, 'food/about.html')


def productDetailPage(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    comments = Comment.objects.all().filter(product_id=product_id)
    product.addView()
    products = Product.objects.all().exclude(id=product_id)
    if request.user.groups.filter(name='Salesman').exists():
        products = products.filter(salesman_id=request.user.salesman.id)
    products = list(products)[:10]
    random.shuffle(products)
    context = {'product': product, 'comments': comments, "products": products}
    if request.session.get('doubleComment'):
        context = {'product': product, 'comments': comments, "products": products,
                   "doubleCommentWarning": request.session['doubleComment']}
        del request.session['doubleComment']
    return render(request, 'food/detalhe.html', context)


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def commentOnItem(request, product_id):
    if request.method == 'POST':
        if Comment.objects.all().filter(user_id=request.user, product_id=product_id).exists():
            request.session['doubleComment'] = "Não pode comentar duas vezes!"
        else:
            commentText = request.POST['commentInput']
            commentRating = request.POST['ratingInput']
            product = Product.objects.get(id=product_id)
            Salesman.objects.get(id=product.salesman_id).addRating(newRating=commentRating)
            product.addRating(newRating=commentRating)
            Comment(user=request.user, text=commentText, dataHour=datetime.datetime.now(), rating=commentRating,
                    product=product).save()
    return HttpResponseRedirect(reverse('food:productDetailPage', args=(product_id,)))


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def deleteProductComment(request, product_id):
    product = Product.objects.get(id=product_id)
    comment = Comment.objects.get(product_id=product_id, user_id=request.user.id)
    if request.method == 'POST':
        Salesman.objects.get(id=product.salesman_id).deleteRating(comment.rating)
        product.deleteRating(comment.rating)
        comment.delete()
    return HttpResponseRedirect(
        request.META.get('HTTP_REFERER', '/'))  # volta para a página anterior. necessário por causa do perfil


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def updateProductComment(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    comment = Comment.objects.get(product_id=product_id, user_id=request.user.id)
    if request.method == 'POST':
        newText = request.POST['newCommentText']
        newRating = request.POST['newCommentRating']
        product.updateRating(comment.rating, newRating)
        Salesman.objects.get(id=product.salesman_id).updateRating(newRating=newRating, oldRating=newRating)
        Comment.objects.filter(user_id=request.user.id, product_id=product_id).update(text=newText, rating=newRating)
        return HttpResponseRedirect(reverse('food:productDetailPage', args=(product_id,)))
    context = {'product': product, 'comment': comment}
    return render(request, 'food/updateProductComment.html', context)


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Salesman'])
def deleteProduct(request, product_id):
    get_object_or_404(Product, pk=product_id).delete()
    return HttpResponseRedirect(reverse('food:index'))


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Salesman'])
def addProduct(request):
    if request.method == 'POST':
        if request.FILES['myfile']:
            productImage = request.FILES['myfile']
            fs = FileSystemStorage()
            filename = fs.save(productImage.name, productImage)
            uploaded_file_url = fs.url(filename)
            Product.objects.create(name=request.POST.get('productName'),
                                   description=request.POST.get('productDescription'),
                                   price=request.POST.get('productPrice'),
                                   image=uploaded_file_url,
                                   salesman_id=request.user.salesman.id
                                   )
            return HttpResponseRedirect(reverse('food:index'))
    return render(request, 'food/add_product.html')


def get_price(customer):
    shopping_cart = CestoCompras.objects.filter(customer=customer)
    price = 0
    for item in shopping_cart:
        price += item.product.price
    return price


@login_required(login_url="food:loginutilizador")
def pagamento(request):
    user = User.objects.get(id=request.user.id)
    customer = Customer.objects.get(user=user)
    price = get_price(customer)
    if price == 0:
        return render(request, 'food/cestoCompras.html', {'error_message': True})
    return render(request, 'food/pagamento.html', {'price': price})


def checkOut(request):
    user = User.objects.get(id=request.user.id)
    customer = Customer.objects.get(user=user)
    shopping_cart = CestoCompras.objects.filter(customer=customer)
    for item in shopping_cart:
        item.product.sales += 1
        item.product.save()
    price = get_price(customer)
    if customer.credit - price < 0:
        return render(request, 'food/pagamento.html', {'price': price,
                                                       'error_message': "Não tem laterninhas suficientes para esta compra. Vá investir na crypto"})
    else:
        if request.method == 'POST':
            morada = request.POST['morada']
            zipCode = request.POST['ZipCode']
            if morada and zipCode:
                customer.credit = customer.credit - price
                customer.save()
                CestoCompras.objects.filter(customer=customer).delete()
                products = Product.objects.all()
                enviado = "A sua encomenda está confirmada! Será enviada para " + str(morada) + ", " + str(
                    zipCode) + "."
                context = {'products_list': products, 'enviado': enviado}
                return render(request, 'food/index.html', context)
            else:
                return render(request, 'food/pagamento.html', {'price': price,
                                                               'error_message': "Preencha a Morada e o Código Postal"})
    return render(request, 'food/pagamento.html', {'price': price})


@login_required(login_url="food:loginutilizador")
@allowed_users(allowed_roles=['Customer'])
def investCrypto(request):
    user = User.objects.get(id=request.user.id)
    customer = Customer.objects.get(user=user)
    customer.credit = random.randint(1, 1000000)
    customer.save()
    return HttpResponseRedirect(reverse('food:about'))
