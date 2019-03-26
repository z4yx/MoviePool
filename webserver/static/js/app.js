var commonMod = angular.module('commonMod', []);
commonMod.filter('urlencode', function() {
  return window.encodeURIComponent;
});

var indexApp = angular.module('indexApp', ['commonMod']);
indexApp.controller('indexController', function indexController($scope, $http) {
    $http.get("api/pop").success(function(data) {
        data.forEach(function(entry) {
            if (entry.title.length > 20) {
                entry.title = entry.title.substr(0, 20) + "...";
            }
        });
        $scope.results = data;
    });
});
indexApp.filter('reshape', function () {
    return function (input, sub_size) {
        var newArr = [];
        if(!input)return input;
        if(input.reshaped)
            return input.reshaped;
        for(var i=0; i<input.length; i+=sub_size)
            newArr.push(input.slice(i,i+sub_size));
        input.reshaped=newArr;
        return newArr;
    };
});


var searchApp = angular.module('searchApp', ['commonMod']);
searchApp.controller('searchController', function searchController($scope, $http) {
    $http.get("api/search" + location.search).success(function(data) {
        data.forEach(function(entry) {
            if (entry.title.length > 20) {
                entry.title = entry.title.substr(0, 20) + "...";
            }
        });
        $scope.results = data;
    });
});
searchApp.filter('reshape', function () {
    return function (input, sub_size) {
        var newArr = [];
        if(!input)return input;
        if(input.reshaped)
            return input.reshaped;
        for(var i=0; i<input.length; i+=sub_size)
            newArr.push(input.slice(i,i+sub_size));
        input.reshaped=newArr;
        return newArr;
    };
});

var movieApp = angular.module('movieApp', ['commonMod']);

movieApp.controller('movieController', function movieController($scope, $http) {
    function reload_progress(download_id) {
        $http.get('../api/progress/'+download_id).success(function(data){
            console.log(data)
            if(data.reason===0 && $scope.resources.list){
                for (var i = $scope.resources.list.length - 1; i >= 0; i--) {
                    if($scope.resources.list[i].download_id == download_id){
                        $scope.resources.list[i].progress = data.status.progress;
                        $scope.resources.list[i].is_finished = data.status.is_finished;
                    }
                }
            }
        });
    }
    $scope.resources = {ready: false, list: []};
    $scope.download = function(item){
        console.log(item)
        if(item.finished){
            $http.get('../api/download/'+item.download_id).success(function(data){
                console.log(data)
                if(data.reason === 0){
                    // $('#iframe_for_download').prop('src', data.path);
                    window.open(data.path,'_blank');
                }
            });
        }else if(item.progress >= 0){
            // TODO: 注册完成通知
        }else{
            $http.get('../api/cache/'+item.download_id).success(function(data){
                console.log(data)
                if(data.reason === 0){
                    reload_progress(item.download_id);
                }
                // TODO: 注册完成通知
            });
        }
    };
    var pathSegs = location.pathname.split('/');
    $http.get("../api/movie/" + pathSegs[pathSegs.length-1]).success(function(data){
      data.castslist = Array();
      data.casts.forEach(function(entry){
        data.castslist.push(entry.name);
      });
      data.directorslist = Array();
      data.directors.forEach(function(entry){
        data.directorslist.push(entry.name);
      });
      $scope.movie=data;
      $http.get("../api/imdb/" + data.IMDB).success(function(data){
        $scope.imdb=data;
        console.log(data);
      });
    })
    $scope.$watch('movie',function(newValue,oldValue){
        if(newValue && newValue.id){
            $http.get("../api/resources/"+newValue.id).success(function(data){
                $scope.resources.list = data;
                $scope.resources.ready=true;
            });

        }
    });
});
